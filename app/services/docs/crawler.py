"""Crawl vxcloud.io docs and split pages into retrieval chunks.

Pipeline:  seeds (llms.txt + /docs/ + a few product pages) -> BFS over
same-site links under allowed prefixes -> HTML -> sections (one chunk per
heading) with code blocks preserved verbatim.

Code blocks matter most for "how do I ..." questions, so they are emitted as
fenced blocks and never split or re-wrapped. The site renders each terminal
line as a <div> inside <pre> (syntax-highlight spans, no newlines), so lines
are rebuilt from the child <div>s.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("vxthinking.docs.crawler")

BASE_URL = "https://vxcloud.io"
LLMS_TXT = f"{BASE_URL}/docs/llms.txt"

# Path prefixes the crawler may follow. /docs is the canonical source; the
# product pages answer "what is X / pricing / self-hosted" style questions.
DEFAULT_ALLOWED_PREFIXES: Tuple[str, ...] = (
    "/docs",
    "/pages/web/faq",
    "/pages/web/pricing",
    "/pages/web/self-hosted",
    "/pages/web/security",
    "/pages/web/changelog",
    "/pages/web/developer",
    "/pages/web/terraform",
    "/pages/web/cicd",
    "/pages/web/aiagents",
    "/pages/web/vxthinker",
    "/pages/web/agentcontrol",
    "/pages/web/products",
    "/pages/web/multi-cloud-provisioning",
    "/pages/web/ai-devops-platform",
    "/pages/web/ssh-deploy-automation",
)

# Exclude the generated hosting/deploy matrix (5 providers x 10 frameworks of
# near-duplicate pages) and marketplace model cards: they drown real answers.
EXCLUDED_PREFIXES: Tuple[str, ...] = (
    "/pages/web/deploy/",
    "/pages/web/hosting/",
    "/pages/web/marketplace/",
    "/blog/",
)

MAX_CHUNK_CHARS = 2200
MIN_CHUNK_CHARS = 40


@dataclass
class Chunk:
    id: str
    url: str
    page_title: str
    heading_path: List[str]
    text: str                       # markdown, code blocks fenced
    anchor: Optional[str] = None
    code_blocks: List[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return " > ".join([self.page_title, *self.heading_path]) if self.heading_path else self.page_title

    @property
    def source_url(self) -> str:
        return f"{self.url}#{self.anchor}" if self.anchor else self.url

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "url": self.url, "page_title": self.page_title,
            "heading_path": self.heading_path, "text": self.text,
            "anchor": self.anchor, "code_blocks": self.code_blocks,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Chunk":
        return cls(**d)


# ---------------------------------------------------------------------------
# HTML -> chunks
# ---------------------------------------------------------------------------

_NOISE_TAGS = ("script", "style", "noscript", "template", "svg", "button", "nav", "footer", "header", "aside", "form", "iframe")
_WS = re.compile(r"[ \t\r\f\v]+")


def _clean(s: str) -> str:
    return _WS.sub(" ", s.replace("\xa0", " ")).strip()


def _pre_to_code(pre: Tag) -> str:
    """Rebuild a code block.

    The site renders code two ways: <pre><div>line</div>...</pre> (terminal widget) and
    <pre><code><div class=flex><span.select-none>N</span><span>line</span></div>...</code></pre>
    (numbered editor). Both put one line per <div>; gutters are `select-none` spans.
    """
    for gutter in pre.select(".select-none"):
        gutter.decompose()
    container = pre.find("code") or pre
    line_divs = container.find_all("div", recursive=False)
    if line_divs:
        lines = [d.get_text("", strip=False).replace("\xa0", " ").rstrip() for d in line_divs]
    else:
        lines = container.get_text("", strip=False).splitlines()
    return "\n".join(lines).strip("\n")


def _code_caption(pre: Tag) -> str:
    """Label for a code block: the terminal-chrome title or the short <p> right above its widget.
    Only looks inside the block's own widget so a neighbour's label is never borrowed."""
    node: Optional[Tag] = pre
    for _ in range(5):
        node = node.parent if node is not None else None
        if node is None or node.name in ("main", "body"):
            return ""
        if len(node.find_all("pre")) != 1:
            return ""        # ancestor now spans several blocks
        prev = node.find_previous_sibling()
        if prev is not None and prev.name == "p":
            t = _clean(prev.get_text(" "))
            if 0 < len(t) < 80:
                return t
        chrome = node.find("span", class_="truncate")
        if chrome is not None:
            t = _clean(chrome.get_text(" "))
            if 0 < len(t) < 100:
                return t
    return ""


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def html_to_chunks(html: str, url: str) -> List[Chunk]:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:  # pragma: no cover
        soup = BeautifulSoup(html, "html.parser")

    page_title = ""
    if soup.title:
        page_title = _clean(soup.title.get_text(" ")).split("|")[0].strip()
    h1 = soup.find("h1")
    if not page_title and h1:
        page_title = _clean(h1.get_text(" "))

    root = soup.find("main") or soup.find("article") or soup.body or soup
    # Capture code captions before decomposing chrome (the caption <span> lives in the widget).
    captions: Dict[int, str] = {id(pre): _code_caption(pre) for pre in root.find_all("pre")}
    for t in root.find_all(_NOISE_TAGS):
        # keep <pre> content even if wrapped in noise-tagged widgets: only drop non-code noise
        if t.decomposed if hasattr(t, "decomposed") else False:
            continue
        if t.find("pre") is None:
            t.decompose()

    heading_stack: List[Tuple[int, str, Optional[str]]] = []   # (level, text, anchor)
    sections: List[Dict] = []
    cur: Dict = {"path": [], "anchor": None, "parts": [], "code": []}

    def flush() -> None:
        if cur["parts"]:
            sections.append({k: (list(v) if isinstance(v, list) else v) for k, v in cur.items()})
        cur["parts"], cur["code"] = [], []

    seen_pre: Set[int] = set()
    for el in root.descendants:
        if not isinstance(el, Tag):
            continue
        if el.name in ("h2", "h3", "h4"):
            flush()
            level = int(el.name[1])
            text = _clean(el.get_text(" "))
            if not text:
                continue
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            anchor = el.get("id") or _slug(text)
            heading_stack.append((level, text, anchor))
            cur["path"] = [h[1] for h in heading_stack]
            cur["anchor"] = anchor
        elif el.name == "pre" and id(el) not in seen_pre:
            seen_pre.add(id(el))
            code = _pre_to_code(el)
            if not code:
                continue
            cap = captions.get(id(el), "")
            cur["code"].append(code)
            if cap and cur["parts"] and cur["parts"][-1] == cap:
                cur["parts"].pop()          # label was already emitted as a <p>
            cur["parts"].append((f"{cap}:\n" if cap else "") + f"```\n{code}\n```")
        elif el.name in ("p", "li", "td", "th", "dt", "dd", "blockquote") and el.find_parent("pre") is None:
            # skip containers whose text is already emitted via a nested p/li/pre
            if el.find(["p", "li", "pre"]) is not None:
                continue
            t = _clean(el.get_text(" "))
            if t:
                cur["parts"].append(("- " if el.name == "li" else "") + t)
    flush()

    chunks: List[Chunk] = []
    for sec in sections:
        for i, (text, code) in enumerate(_split_section(sec["parts"], sec["code"])):
            if len(text) < MIN_CHUNK_CHARS and not code:
                continue
            cid = f"{urlparse(url).path.strip('/') or 'root'}#{sec['anchor'] or 'top'}:{i}"
            chunks.append(Chunk(id=cid, url=url, page_title=page_title or url, heading_path=sec["path"],
                                text=text, anchor=sec["anchor"], code_blocks=code))
    return chunks


# ---------------------------------------------------------------------------
# Next.js flight payload (CLI command reference, SDK module examples)
# ---------------------------------------------------------------------------
# The CLI/SDK reference pages render their per-command docs client-side from props embedded in
# `self.__next_f.push([1,"..."])`. None of it is in the static DOM, so we read the props directly.

_PUSH = re.compile(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)')
_DECODER = json.JSONDecoder()


def _flight_text(html: str) -> str:
    out = []
    for m in _PUSH.finditer(html):
        try:
            out.append(json.loads(m.group(1)))
        except Exception:
            continue
    return "".join(out)


def _flight_objects(html: str, lead: str) -> Iterable[dict]:
    """Decode every JSON object in the flight text that starts with `lead` (e.g. '{"namespace":').

    Schema-driven rather than row-driven: text-chunk rows are glued to the next row without a
    newline, so splitting on lines drops objects.
    """
    text = _flight_text(html)
    pos = 0
    while (i := text.find(lead, pos)) != -1:
        try:
            obj, end = _DECODER.raw_decode(text, i)
        except ValueError:
            pos = i + len(lead)
            continue
        if isinstance(obj, dict):
            yield obj
        pos = end


def _fence(code: str, lang: str = "") -> str:
    return f"```{lang}\n{code.strip(chr(10))}\n```"


def flight_chunks(html: str, url: str, page_title: str) -> List[Chunk]:
    chunks: List[Chunk] = []
    seen: Set[str] = set()
    base = urlparse(url).path.strip("/") or "root"

    def add(heading: List[str], anchor: str, text: str, code: List[str]) -> None:
        cid = f"{base}#{anchor}:flight"
        if cid in seen or len(text) < MIN_CHUNK_CHARS:
            return
        seen.add(cid)
        chunks.append(Chunk(id=cid, url=url, page_title=page_title, heading_path=heading,
                            text=text, anchor=anchor, code_blocks=code))

    def visit(d: dict) -> None:
        # CLI group: {"namespace": "...", "commands": [{"name","description","usage","flags","examples"...}]}
        if isinstance(d.get("commands"), list) and d.get("namespace"):
            for c in d["commands"]:
                if not isinstance(c, dict) or not c.get("name"):
                    continue
                parts = [f"{c['name']} — {c.get('description', '')}".strip(" —")]
                if c.get("usage"):
                    parts.append(f"Usage: {c['usage']}")
                flags = [f for f in c.get("flags", []) if isinstance(f, dict) and f.get("flag")]
                if flags:
                    parts.append("Flags:\n" + "\n".join(f"- {f['flag']}: {f.get('description', '')}" for f in flags))
                code: List[str] = []
                exs = [e for e in c.get("examples", []) if isinstance(e, dict) and e.get("code")]
                if not exs and c.get("example"):
                    exs = [{"label": "Example", "language": "bash", "code": c["example"]}]
                for e in exs:
                    code.append(e["code"].strip("\n"))
                    parts.append(f"{e.get('label', 'Example')}:\n" + _fence(e["code"], e.get("language", "")))
                add([d["namespace"], c["name"]], _slug(c["name"]), "\n".join(parts), code)
        # SDK module: {"module": "...", "description": "...", "examples": [{"label","code"}]}
        elif d.get("module") and isinstance(d.get("examples"), list):
            parts = [f"{d['module']} — {d.get('description', '')}".strip(" —")]
            code = []
            for e in d["examples"]:
                if isinstance(e, dict) and e.get("code"):
                    code.append(e["code"].strip("\n"))
                    parts.append(f"{e.get('label', 'Example')}:\n" + _fence(e["code"], e.get("language", "")))
            add([str(d["module"])], _slug(str(d["module"])), "\n".join(parts), code)

    for lead in ('{"namespace":', '{"module":'):
        for obj in _flight_objects(html, lead):
            visit(obj)
    return chunks


def _split_section(parts: List[str], code: List[str]) -> Iterable[Tuple[str, List[str]]]:
    """Group parts into <= MAX_CHUNK_CHARS chunks; never split inside a part (code stays whole)."""
    buf: List[str] = []
    size = 0
    for p in parts:
        if buf and size + len(p) > MAX_CHUNK_CHARS:
            body = "\n".join(buf)
            yield body, [c for c in code if c in body]
            buf, size = [], 0
        buf.append(p)
        size += len(p) + 1
    if buf:
        body = "\n".join(buf)
        yield body, [c for c in code if c in body]


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

def _allowed(path: str, prefixes: Tuple[str, ...]) -> bool:
    if any(path.startswith(x) for x in EXCLUDED_PREFIXES):
        return False
    return any(path == p or path.startswith(p.rstrip("/") + "/") or path.startswith(p) for p in prefixes)


def _norm(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    path = p.path or "/"
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return f"{p.scheme}://{p.netloc}{path}"


def llms_txt_to_chunks(text: str, url: str) -> List[Chunk]:
    """/docs/llms.txt is curated markdown (auth header, token prefixes, doc map): index it by `##` section."""
    chunks: List[Chunk] = []
    heading, buf = "Overview", []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if len(body) >= MIN_CHUNK_CHARS:
            chunks.append(Chunk(id=f"llms.txt#{_slug(heading)}:{len(chunks)}", url=url, page_title="VxCloud Documentation (llms.txt)",
                                heading_path=[heading], text=body, anchor=None))

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            heading, buf = line[3:].strip(), []
        elif not line.startswith("# "):
            buf.append(line)
    flush()
    return chunks


def extract_links(html: str, page_url: str, base_host: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    out: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        full = urljoin(page_url, href)
        if urlparse(full).netloc != base_host:
            continue
        out.append(_norm(full))
    return out


_MD_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")


async def crawl(
    base_url: str = BASE_URL,
    *,
    prefixes: Tuple[str, ...] = DEFAULT_ALLOWED_PREFIXES,
    max_pages: int = 400,
    concurrency: int = 8,
    timeout: float = 20.0,
    client=None,
) -> Tuple[List[Chunk], Dict[str, str]]:
    """Crawl and return (chunks, errors-by-url)."""
    import httpx

    host = urlparse(base_url).netloc
    errors: Dict[str, str] = {}
    own_client = client is None
    client = client or httpx.AsyncClient(
        follow_redirects=True, timeout=timeout,
        headers={"User-Agent": "VxThinkingDocsBot/1.0 (+https://vxcloud.io)", "Accept-Encoding": "gzip, deflate"},
    )
    seeds: List[str] = [f"{base_url}/docs/"]
    try:
        r = await client.get(f"{base_url}/docs/llms.txt")
        if r.status_code == 200:
            seeds += [_norm(u) for u in _MD_LINK.findall(r.text) if urlparse(u).netloc == host]
    except Exception as e:  # llms.txt is a hint, not a requirement
        errors[f"{base_url}/docs/llms.txt"] = str(e)
    seeds += [f"{base_url}{p.rstrip('/')}/" for p in prefixes if not p.startswith("/docs")]

    seen: Set[str] = set()
    queue: List[str] = []
    for s in seeds:
        n = _norm(s)
        if n not in seen and _allowed(urlparse(n).path, prefixes):
            seen.add(n)
            queue.append(n)

    chunks: List[Chunk] = []
    sem = asyncio.Semaphore(concurrency)

    async def fetch(u: str) -> Optional[str]:
        async with sem:
            try:
                r = await client.get(u)
                ctype = r.headers.get("content-type", "")
                if r.status_code == 200 and u.endswith("llms.txt"):
                    return r.text
                if r.status_code != 200 or "text/html" not in ctype:
                    errors[u] = f"HTTP {r.status_code}"
                    return None
                return r.text
            except Exception as e:
                errors[u] = str(e)
                return None

    try:
        i = 0
        while i < len(queue) and i < max_pages:
            batch = queue[i:i + concurrency * 2]
            i += len(batch)
            pages = await asyncio.gather(*(fetch(u) for u in batch))
            for u, html in zip(batch, pages):
                if not html:
                    continue
                if u.endswith("llms.txt"):
                    chunks.extend(llms_txt_to_chunks(html, u))
                    continue
                page_chunks = html_to_chunks(html, u)
                title = page_chunks[0].page_title if page_chunks else u
                chunks.extend(page_chunks)
                chunks.extend(flight_chunks(html, u, title))
                for link in extract_links(html, u, host):
                    if link not in seen and _allowed(urlparse(link).path, prefixes) and len(seen) < max_pages * 2:
                        seen.add(link)
                        queue.append(link)
        logger.info("crawled %d pages -> %d chunks (%d errors)", min(i, len(queue)), len(chunks), len(errors))
    finally:
        if own_client:
            await client.aclose()
    return chunks, errors
