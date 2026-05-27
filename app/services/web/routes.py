"""FastAPI routes for the web-knowledge service.

Mounted at /v1/web by app/app.py.

    POST /v1/web/scrape   -- fetch + extract a single URL
    POST /v1/web/search   -- query -> ranked URL list
    POST /v1/web/context  -- query -> compact LLM-ready context string
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from .knowledge import fetch_external_context, scrape_url
from .searcher import web_search

logger = logging.getLogger("VxThinkingLLM.web.routes")
router = APIRouter(prefix="/v1/web", tags=["web"])


class ScrapeUrlRequest(BaseModel):
    url: HttpUrl
    use_playwright: bool = False
    max_chars: int = Field(20_000, ge=500, le=200_000)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(5, ge=1, le=20)


class ContextRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_pages: int = Field(3, ge=1, le=8)
    max_chars_per_page: int = Field(2_000, ge=200, le=20_000)
    total_chars_budget: int = Field(8_000, ge=500, le=40_000)


@router.post("/scrape")
async def scrape(req: ScrapeUrlRequest) -> dict:
    """Fetch + extract a single URL."""
    start = time.perf_counter()
    try:
        result = await scrape_url(
            str(req.url),
            max_chars=req.max_chars,
            use_playwright=req.use_playwright,
        )
    except Exception as exc:
        logger.warning("scrape_url failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"scrape failed: {exc}")
    payload = result.model_dump()
    payload["duration_ms"] = (time.perf_counter() - start) * 1000
    return payload


@router.post("/search")
async def search(req: SearchRequest) -> dict:
    """Search the web for `query`, return up to `limit` ranked hits."""
    start = time.perf_counter()
    hits = await web_search(req.query, limit=req.limit)
    return {
        "query": req.query,
        "count": len(hits),
        "results": [h.model_dump() for h in hits],
        "duration_ms": (time.perf_counter() - start) * 1000,
    }


@router.post("/context")
async def context(req: ContextRequest) -> dict:
    """Search → scrape top N → return LLM-ready context string + sources."""
    start = time.perf_counter()
    out = await fetch_external_context(
        req.query,
        max_pages=req.max_pages,
        max_chars_per_page=req.max_chars_per_page,
        total_chars_budget=req.total_chars_budget,
    )
    out["duration_ms"] = (time.perf_counter() - start) * 1000
    out["chars"] = len(out.get("context", ""))
    return out
