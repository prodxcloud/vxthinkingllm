"""Web-knowledge service — refactored from va_fastapiclient/.../webscraper.

Public entry points:
    fetch_external_context(query)   -- async: search → scrape → context string
    scrape_url(url)                 -- async: fetch + extract a single URL
    web_search(query)               -- async: query → ranked URLs
    router                          -- FastAPI router mounted at /v1/web

Used by VxThinking and VxSupport as a fallback when local FAISS
retrieval can't answer a question.
"""

from .knowledge import fetch_external_context, scrape_url
from .models import (
    ContactInfo,
    LinkInfo,
    MediaAsset,
    PageMetadata,
    ScrapeResult,
    SearchHit,
    TableData,
)
from .routes import router
from .searcher import web_search

__all__ = [
    "ContactInfo",
    "LinkInfo",
    "MediaAsset",
    "PageMetadata",
    "ScrapeResult",
    "SearchHit",
    "TableData",
    "fetch_external_context",
    "router",
    "scrape_url",
    "web_search",
]
