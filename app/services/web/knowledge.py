"""High-level knowledge fallback for VxThinking and VxSupport.

When local FAISS retrieval comes up empty (or low-confidence), the
LLM routes can call `fetch_external_context(query)` to get a concise,
LLM-ready string built from live web search + scrape.

This is intentionally async-first.  All network calls are best-effort:
if anything fails (offline, rate-limited, no Playwright, etc.), it
returns whatever it managed to gather, with diagnostics in `errors`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .extractors import run_extractors
from .fetchers import fetch_with_fallback
from .models import ScrapeResult, SearchHit
from .searcher import web_search

logger = logging.getLogger("VxThinkingLLM.web.knowledge")

DEFAULT_MAX_PAGES = 3
DEFAULT_MAX_CHARS_PER_PAGE = 2_000
DEFAULT_TOTAL_CHARS_BUDGET = 8_000


async def scrape_url(url: str, *, max_chars: int = 20_000, use_playwright: bool = False) -> ScrapeResult:
    """Fetch + extract a single URL.  Always returns a ScrapeResult."""
    fetch = await fetch_with_fallback(url, use_playwright=use_playwright)
    html = fetch.get("html") or ""
    result = ScrapeResult(
        url=url,
        final_url=fetch.get("final_url") or url,
        status="success" if html else "failed",
        status_code=fetch.get("status_code"),
        fetcher=fetch.get("fetcher", "httpx"),
        load_time_ms=fetch.get("load_time_ms"),
        errors=list(fetch.get("errors") or []),
    )
    if not html:
        result.status = "failed"
        return result

    try:
        extracted = run_extractors(
            html,
            url=result.final_url or url,
            extract=["text", "metadata", "links", "contacts"],
            max_chars=max_chars,
        )
    except Exception as exc:
        logger.warning("extractors failed for %s: %s", url, exc)
        result.status = "partial"
        result.errors.append(f"extractors failed: {exc}")
        return result

    if "metadata" in extracted:
        result.metadata = extracted["metadata"]
    result.text = extracted.get("text", "")
    result.word_count = extracted.get("word_count", 0)
    result.reading_time_minutes = extracted.get("reading_time_minutes", 0.0)
    if "links" in extracted:
        result.links = extracted["links"]
    if "contacts" in extracted:
        result.contacts = extracted["contacts"]
    return result


async def fetch_external_context(
    query: str,
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_chars_per_page: int = DEFAULT_MAX_CHARS_PER_PAGE,
    total_chars_budget: int = DEFAULT_TOTAL_CHARS_BUDGET,
) -> Dict[str, Any]:
    """Search the web for `query`, scrape top results, return LLM-ready context.

    Returns:
        {
            "query": str,
            "context": str   # ready to drop into an LLM prompt
            "sources": [{"title": str, "url": str, "snippet": str}],
            "errors": [str],
        }
    """
    out: Dict[str, Any] = {"query": query, "context": "", "sources": [], "errors": []}
    hits: List[SearchHit] = []
    try:
        hits = await web_search(query, limit=max_pages * 2)
    except Exception as exc:
        out["errors"].append(f"search failed: {exc}")
        return out
    if not hits:
        out["errors"].append("no search results")
        return out

    # Scrape the top N concurrently
    targets = hits[:max_pages]
    scrapes = await asyncio.gather(
        *(scrape_url(h.url, max_chars=max_chars_per_page) for h in targets),
        return_exceptions=True,
    )

    pieces: List[str] = []
    used_chars = 0
    for hit, sc in zip(targets, scrapes):
        if isinstance(sc, Exception):
            out["errors"].append(f"{hit.url}: {sc}")
            continue
        if not isinstance(sc, ScrapeResult) or not sc.text:
            continue
        title = (sc.metadata.title or hit.title or sc.final_url or hit.url)[:200]
        snippet = sc.text[:max_chars_per_page]
        if used_chars + len(snippet) > total_chars_budget:
            snippet = snippet[: max(0, total_chars_budget - used_chars)]
        if not snippet:
            break
        used_chars += len(snippet)
        pieces.append(f"### Source: {title}\n### URL: {sc.final_url or hit.url}\n\n{snippet}")
        out["sources"].append({"title": title, "url": sc.final_url or hit.url, "snippet": hit.snippet})

    out["context"] = "\n\n---\n\n".join(pieces)
    return out
