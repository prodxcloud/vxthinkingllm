"""Hybrid-ready docs index.

BM25 over title + heading path + body, in pure Python (no new dependency, no model
download, deterministic). Exact-term matching is what "vxcli auth login" style
questions need; dense retrieval via the existing FAISS `VectorStore` can be fused in
through `DocIndex.search(..., dense=...)` without changing callers.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .crawler import Chunk

_TOKEN = re.compile(r"[a-z0-9]+(?:[._/-][a-z0-9]+)*")
_STOP = frozenset(
    "a an and are as at be by can do does for from how i in is it its me my of on or the to we what when where which with you your "
    "should would could there this that these those into onto about get use using much many lot".split()
)
# Cheap query-side synonyms for how people phrase things vs how the docs do.
_SYNONYMS = {
    "setup": ["install", "configure"], "download": ["install"],
    "login": ["auth"], "signin": ["auth", "login"],
    # Users commonly call the developer API token an "API key".
    "key": ["token"], "keys": ["token"],
    "cli": ["vxcli"], "terminal": ["vxcli"],
    # pricing phrasing: users ask "how much does it cost", docs say "pricing"/"plan".
    # Values are stemmed forms so they match the corpus (pricing/price -> "pric").
    "cost": ["pric", "plan"], "costs": ["pric", "plan"], "price": ["pric", "plan"],
    "pricing": ["plan"], "subscription": ["plan", "bill"],
    "cheap": ["pric", "plan"], "cheapest": ["pric", "plan"], "affordable": ["pric", "plan"],
    "expensive": ["pric", "plan"],
}


_SUFFIXES = ("ations", "ation", "ition", "ments", "ment", "ings", "ing", "ate", "ed", "es", "s", "e")


def stem(tok: str) -> str:
    """Crude suffix stripper: installation/installing/installed -> install; authenticate/authentication -> authentic."""
    if len(tok) <= 4 or not tok.isalpha():
        return tok
    for suf in _SUFFIXES:
        if tok.endswith(suf) and len(tok) - len(suf) >= 4:
            return tok[: -len(suf)]
    return tok


def tokenize(text: str, *, expand: bool = False) -> List[str]:
    text = re.sub(r"\b(?:log|sign)[\s-]?in\b", "login", text.lower())
    out: List[str] = []
    for tok in _TOKEN.findall(text):
        parts = re.split(r"[._/-]", tok)
        out.append(tok)
        if len(parts) > 1:
            out.extend(p for p in parts if p)
    out = [stem(t) for t in out if t not in _STOP and len(t) > 1]
    if expand:
        for t in list(out):
            out.extend(_SYNONYMS.get(t, []))
    return out


class DocIndex:
    K1 = 1.4
    B = 0.75
    # Field weights realised by repeating tokens: heading text is a far stronger signal than body.
    TITLE_W, HEADING_W = 2, 3

    def __init__(self, chunks: Optional[Sequence[Chunk]] = None):
        self.chunks: List[Chunk] = []
        self._tf: List[Counter] = []
        self._len: List[int] = []
        self._df: Dict[str, int] = defaultdict(int)
        self._postings: Dict[str, List[int]] = defaultdict(list)
        self._avg = 0.0
        if chunks:
            self.build(chunks)

    # -- build / persist ----------------------------------------------------
    def build(self, chunks: Sequence[Chunk]) -> int:
        self.chunks = list(chunks)
        self._tf, self._len = [], []
        self._df, self._postings = defaultdict(int), defaultdict(list)
        for i, c in enumerate(self.chunks):
            slug = urlparse(c.url).path.replace("/docs", " ").replace("/pages/web", " ")   # store-secrets-in-vault -> store secrets vault
            toks = (
                tokenize(c.page_title) * self.TITLE_W
                + tokenize(slug) * self.TITLE_W
                + tokenize(" ".join(c.heading_path)) * self.HEADING_W
                + tokenize(c.text)
            )
            tf = Counter(toks)
            self._tf.append(tf)
            self._len.append(len(toks))
            for t in tf:
                self._df[t] += 1
                self._postings[t].append(i)
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0
        return len(self.chunks)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "chunks": [c.to_dict() for c in self.chunks]}), encoding="utf-8")
        tmp.replace(path)          # atomic: readers never see a half-written index

    @classmethod
    def load(cls, path: Path) -> "DocIndex":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Chunk.from_dict(d) for d in data["chunks"]])

    def __len__(self) -> int:
        return len(self.chunks)

    # -- search -------------------------------------------------------------
    def _bm25(self, q_tokens: List[str]) -> Dict[int, float]:
        n = len(self.chunks)
        scores: Dict[int, float] = defaultdict(float)
        for t in set(q_tokens):
            df = self._df.get(t, 0)
            if not df:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for i in self._postings[t]:
                f = self._tf[i][t]
                denom = f + self.K1 * (1 - self.B + self.B * self._len[i] / (self._avg or 1))
                scores[i] += idf * f * (self.K1 + 1) / denom
        return scores

    def idf(self, t: str) -> float:
        n, df = len(self.chunks), self._df.get(t, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def coverage(self, query: str, chunk_idx: int) -> float:
        """Fraction of the query's information (idf mass) present in the chunk. Terms the corpus has
        never seen count as fully missing, which is what makes off-topic questions fail the gate."""
        q = set(tokenize(query))          # the user's own words (unexpanded)
        if not q:
            return 0.0
        tf = self._tf[chunk_idx]
        # A term counts as present if it, or one of its synonyms, is in the chunk — so
        # "cost" is covered by a chunk that says "pricing"/"plan". Off-topic words have no
        # synonym and must appear literally, which is what still makes junk queries fail.
        def present(t: str) -> bool:
            return bool(tf.get(t)) or any(tf.get(s) for s in _SYNONYMS.get(t, ()))
        total = sum(self.idf(t) if t in self._df else self.idf("") for t in q)
        got = sum(self.idf(t) for t in q if present(t))
        return got / total if total else 0.0

    def search(
        self,
        query: str,
        k: int = 5,
        *,
        dense: Optional[Callable[[str, int], List[Tuple[int, float]]]] = None,
    ) -> List[Dict]:
        """Return top-k [{chunk, score}]. `dense(query, k) -> [(chunk_idx, score)]` is fused via RRF."""
        q = tokenize(query, expand=True)
        if not q or not self.chunks:
            return []
        sparse = self._bm25(q)

        # Light prior: official /docs pages beat marketing pages; code-bearing chunks win "how do I" queries.
        wants_howto = bool(re.search(r"\b(how|install|setup|set up|run|command|deploy|login|configure)\b", query.lower()))
        for i in list(sparse):
            c = self.chunks[i]
            if "/docs" in c.url:
                sparse[i] *= 1.15
            if wants_howto and c.code_blocks:
                sparse[i] *= 1.2

        # Heading precision: a section whose own heading is (mostly) covered by the query is what
        # the user asked about; "Installation" must beat "Install services from the catalog".
        qset = set(q)
        for i in list(sparse):
            c = self.chunks[i]
            leaf = tokenize(c.heading_path[-1]) if c.heading_path else []
            if leaf:
                sparse[i] *= 1 + 0.8 * (sum(t in qset for t in leaf) / len(leaf))

        # Product affinity: the combined index holds both VxCloud and SalesShift docs,
        # which share same-named pages (/docs/cli, /docs/sdks). When the query names one
        # product by brand, prefer that product's pages and demote the other's — the same
        # signal the /v1/ask dispatcher routes on. Queries that name neither are left to
        # pure BM25 (product-specific vocab like "sequence"/"provision VM" self-separates).
        ql = query.lower()
        wants_ss = "salesshift" in ql or "sales shift" in ql
        # Auth questions are especially prone to generic "set up" chunks
        # outranking the actual token instructions. Prefer sections whose
        # title/body explicitly discusses API keys or tokens.
        wants_api_auth = bool(re.search(r"\b(api\s+key|api\s+token|developer\s+key|access\s+token)\b", ql))
        if wants_api_auth:
            for i in list(sparse):
                c = self.chunks[i]
                auth_text = f"{c.page_title} {' '.join(c.heading_path)} {c.text}".lower()
                if re.search(r"\b(api\s+(?:key|token)|developer\s+api\s+key|generate an api token|x-api-key)\b", auth_text):
                    sparse[i] *= 2.0
                elif "salesshift" in auth_text and "sending" in auth_text:
                    sparse[i] *= 0.35
        # Broad definition questions should prefer the product overview rather
        # than an incidental CLI command such as `salesshift stats`.
        wants_definition = bool(re.search(r"\bwhat(?:\s+is|'s)\b|\babout\b|\boverview\b", ql))
        if wants_definition and wants_ss:
            for i in list(sparse):
                c = self.chunks[i]
                text = f"{c.page_title} {' '.join(c.heading_path)} {c.text}".lower()
                if any(term in text for term in ("crm", "outbound", "prospect", "quote-to-cash", "sales platform", "sales product")):
                    sparse[i] *= 2.2
                if "vxcli" in c.page_title.lower() or "vxcli" in " ".join(c.heading_path).lower():
                    sparse[i] *= 0.45
        wants_vx = any(t in ql for t in ("vxcli", "vxcloud", "prodxcloud", "vxsdk", "vxthink", "vxnode"))
        if wants_vx != wants_ss:   # exactly one product named
            for i in list(sparse):
                is_ss = "salesshift" in urlparse(self.chunks[i].url).netloc
                sparse[i] *= 1.6 if is_ss == wants_ss else 0.55

        ranked = sorted(sparse.items(), key=lambda kv: kv[1], reverse=True)
        if dense is not None:
            fused: Dict[int, float] = defaultdict(float)
            for rank, (i, _) in enumerate(ranked[: k * 4]):
                fused[i] += 1.0 / (60 + rank)
            for rank, (i, _) in enumerate(dense(query, k * 4)):
                fused[i] += 1.0 / (60 + rank)
            top = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]
            raw = dict(ranked)
            return [{"chunk": self.chunks[i], "score": raw.get(i, 0.0), "fused": s, "coverage": self.coverage(query, i)} for i, s in top]
        return [{"chunk": self.chunks[i], "score": s, "coverage": self.coverage(query, i)} for i, s in ranked[:k]]
