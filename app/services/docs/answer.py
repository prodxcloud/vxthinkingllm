"""Grounded answering over the docs index.

Two modes, chosen per request (`DOCS_ANSWER_MODE=auto|llm|extractive`):

* extractive  – no generation. Returns the best-matching sections with their code
  blocks verbatim. Exact commands can never be hallucinated. Used automatically when the
  loaded model has no chat template (e.g. the distilgpt2 fallback) or fails.
* llm         – the retrieved sections are put in the prompt and the model is told to
  answer only from them, cite sources, and say so when the docs don't cover the question.

Both return the same shape, always including `sources`, so callers/UI can link out.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional

from .index import DocIndex

logger = logging.getLogger("vxthinking.docs.answer")

# BM25 scores are corpus-relative; this floor was tuned on the gold set (scripts/eval_docs.py).
MIN_SCORE = float(os.getenv("DOCS_MIN_SCORE", "4.0"))
MIN_COVERAGE = float(os.getenv("DOCS_MIN_COVERAGE", "0.5"))
MAX_CONTEXT_CHARS = int(os.getenv("DOCS_MAX_CONTEXT_CHARS", "6000"))

SYSTEM_PROMPT = (
    "You are VxThinking, the documentation assistant for VxCloud (vxcloud.io), a multi-cloud DevOps "
    "platform with the vxcli CLI, REST API and Python/TypeScript/Go SDKs.\n"
    "Rules:\n"
    "1. Answer ONLY from the numbered DOCS excerpts below. Never invent commands, flags, URLs or versions.\n"
    "2. Copy commands exactly as written in the excerpts, in fenced code blocks, and say which OS/shell each is for.\n"
    "3. Give the answer first, then short numbered steps, then how to verify it worked.\n"
    "4. Cite excerpts like [1], [2].\n"
    "5. If the excerpts do not contain the answer, say \"That isn't covered in the VxCloud docs I have\" and point to https://vxcloud.io/docs."
)

NOT_FOUND = (
    "That isn't covered in the VxCloud docs I have. Try rephrasing, or browse https://vxcloud.io/docs "
    "(CLI: https://vxcloud.io/docs/cli, API: https://vxcloud.io/docs/api, SDKs: https://vxcloud.io/docs/sdks)."
)

GenerateFn = Callable[[str, str, int], Optional[str]]   # (system, user, max_new_tokens) -> text | None


def _sources(hits: List[Dict]) -> List[Dict[str, Any]]:
    seen, out = set(), []
    for h in hits:
        c = h["chunk"]
        if c.source_url in seen:
            continue
        seen.add(c.source_url)
        out.append({"title": c.title, "url": c.source_url, "score": round(float(h["score"]), 3)})
    return out


def _build_context(hits: List[Dict]) -> str:
    parts, used = [], 0
    for n, h in enumerate(hits, 1):
        c = h["chunk"]
        block = f"[{n}] {c.title}\nURL: {c.source_url}\n{c.text}"
        if used + len(block) > MAX_CONTEXT_CHARS:
            block = block[: max(0, MAX_CONTEXT_CHARS - used)]
        if not block:
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)


def _extractive(hits: List[Dict]) -> str:
    """Best section verbatim (+ pointers to runners-up). Commands come straight from the docs."""
    top = hits[0]["chunk"]
    out = [f"From **{top.title}**:\n", top.text]
    extra = [h["chunk"] for h in hits[1:3]]
    if extra:
        out.append("\nRelated:")
        out += [f"- {c.title} — {c.source_url}" for c in extra]
    out.append(f"\nSource: {top.source_url}")
    return "\n".join(out)


def answer(
    question: str,
    index: DocIndex,
    *,
    k: int = 4,
    mode: Optional[str] = None,
    generate: Optional[GenerateFn] = None,
    max_new_tokens: int = 500,
    dense=None,
) -> Dict[str, Any]:
    mode = (mode or os.getenv("DOCS_ANSWER_MODE", "auto")).lower()
    hits = index.search(question, k=k, dense=dense)
    best_cov = max((h["coverage"] for h in hits), default=0.0)
    if not hits or hits[0]["score"] < MIN_SCORE or best_cov < MIN_COVERAGE:
        return {"answer": NOT_FOUND, "mode": "not_found", "grounded": False,
                "sources": [], "top_score": hits[0]["score"] if hits else 0.0}

    sources = _sources(hits)
    text: Optional[str] = None
    used = "extractive"
    if mode in ("auto", "llm") and generate is not None:
        user = f"DOCS:\n{_build_context(hits)}\n\nQUESTION: {question}"
        try:
            text = generate(SYSTEM_PROMPT, user, max_new_tokens)
        except Exception as e:  # never fail the request because generation failed
            logger.warning("generation failed, falling back to extractive: %s", e)
            text = None
        if text and _is_grounded(text, hits):
            used = "llm"
        else:
            text = None
    if text is None:
        text = _extractive(hits)
    return {"answer": text, "mode": used, "grounded": True, "sources": sources, "top_score": hits[0]["score"]}


_CMD_LIKE = re.compile(r"(?<![\w/.\-])(?:curl|irm|wget|sudo|vxcli|pip3?|npm|npx|yarn|go get|go install|terraform|docker|kubectl|brew)\s[^\n`]+")


def _is_grounded(text: str, hits: List[Dict]) -> bool:
    """Reject generations whose commands don't appear in the retrieved excerpts."""
    corpus = " ".join(h["chunk"].text for h in hits)
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    corpus_n = norm(corpus)
    for m in _CMD_LIKE.finditer(text):
        cmd = norm(m.group(0))
        if cmd and cmd not in corpus_n:
            logger.info("dropping generation: command not in context: %r", cmd)
            return False
    return True
