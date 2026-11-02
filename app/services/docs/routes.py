"""Docs Q&A routes, mounted at /v1/docs.

    POST /v1/docs/ask      question -> grounded answer + sources
    POST /v1/docs/search   query -> ranked sections (no generation)
    GET  /v1/docs/health   index status
    POST /v1/docs/reindex  re-crawl vxcloud.io (requires X-Admin-Token == $VXDOCS_ADMIN_TOKEN)
"""

from __future__ import annotations

import asyncio
import hmac
import os
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .answer import answer
from .service import DocsService

router = APIRouter(prefix="/v1/docs", tags=["docs"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    k: int = Field(4, ge=1, le=10)
    mode: Optional[str] = Field(None, pattern="^(auto|llm|extractive)$")
    max_new_tokens: int = Field(500, ge=32, le=2048)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    k: int = Field(5, ge=1, le=20)


def get_service(req: Request) -> DocsService:
    svc = getattr(req.app.state, "docs", None)
    if svc is None:
        raise HTTPException(503, "docs service not initialised")
    return svc


def make_generate_fn(app) -> Optional[Any]:
    """Adapt the loaded specialist backend to the (system, user, n) -> text signature."""
    backend = getattr(app.state, "cloudllm", None)
    if backend is None or not getattr(backend, "loaded", False) or not hasattr(backend, "chat"):
        return None
    return backend.chat


async def run_answer(app, svc: DocsService, question: str, **kw) -> Dict[str, Any]:
    # Generation is blocking torch code: keep it off the event loop.
    return await asyncio.to_thread(answer, question, svc.index, generate=make_generate_fn(app), **kw)


@router.get("/health")
async def health(req: Request) -> Dict[str, Any]:
    svc = get_service(req)
    return {"status": "healthy" if svc.ready else "degraded", **svc.stats()}


@router.post("/ask")
async def ask(body: AskRequest, req: Request) -> Dict[str, Any]:
    svc = get_service(req)
    if not svc.ready:
        raise HTTPException(503, "docs index not built yet; run `python -m app.services.docs.build` or POST /v1/docs/reindex")
    t0 = time.perf_counter()
    out = await run_answer(req.app, svc, body.question, k=body.k, mode=body.mode, max_new_tokens=body.max_new_tokens)
    out["question"] = body.question
    out["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out


@router.post("/search")
async def search(body: SearchRequest, req: Request) -> Dict[str, Any]:
    svc = get_service(req)
    hits = svc.index.search(body.query, k=body.k)
    return {"query": body.query, "results": [
        {"title": h["chunk"].title, "url": h["chunk"].source_url, "score": round(h["score"], 3),
         "text": h["chunk"].text} for h in hits]}


@router.post("/reindex")
async def reindex(req: Request, x_admin_token: Optional[str] = Header(None)) -> Dict[str, Any]:
    expected = os.getenv("VXDOCS_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(403, "reindex disabled: set VXDOCS_ADMIN_TOKEN")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(401, "invalid admin token")
    return await get_service(req).reindex()
