"""Lightweight web search — query → ranked URL list.

Uses DuckDuckGo's HTML endpoint (no API key, no JS required). The HTML
shape is somewhat fragile but stable enough for a fallback knowledge
path.  Falls back to an empty list on any error so callers don't crash.
"""

from __future__ import annotations

import logging
from typing import List
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

from bs4 import BeautifulSoup

from .fetchers import httpx_fetch
from .models import SearchHit

logger = logging.getLogger("VxThinkingLLM.web.searcher")

DDG_HTML = "https://html.duckduckgo.com/html/?q={q}"


def _unwrap_ddg_redirect(href: str) -> str:
    """DDG wraps result links as `/l/?uddg=<encoded-target>`. Unwrap to the real URL."""
    if not href:
        return href
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if parsed.path == "/l/" and parsed.query:
        qs = parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            return unquote(qs["uddg"][0])
    return href


async def web_search(query: str, *, limit: int = 5) -> List[SearchHit]:
    """Return up to `limit` SearchHits for `query`. Empty list on error."""
    if not query or not query.strip():
        return []
    url = DDG_HTML.format(q=quote_plus(query.strip()))
    try:
        html, status, _ = await httpx_fetch(url, timeout=15.0)
    except Exception as exc:
        logger.info("web_search httpx failed for %r: %s", query, exc)
        return []
    if status != 200 or not html:
        return []

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    hits: List[SearchHit] = []
    for i, result in enumerate(soup.select("div.result, div.web-result")):
        a = result.select_one("a.result__a, h2 a")
        if not a:
            continue
        href = _unwrap_ddg_redirect(a.get("href", ""))
        if not href.startswith(("http://", "https://")):
            continue
        title = a.get_text(strip=True)[:300]
        snippet_el = result.select_one(".result__snippet, .result__body")
        snippet = (snippet_el.get_text(" ", strip=True)[:500]) if snippet_el else ""
        hits.append(SearchHit(title=title, url=href, snippet=snippet, rank=i + 1))
        if len(hits) >= limit:
            break

    logger.info("web_search %r -> %d hits", query, len(hits))
    return hits
