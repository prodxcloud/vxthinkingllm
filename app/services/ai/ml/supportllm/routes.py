"""
VxSupport routes — /v1/support

Exposes:
    POST /v1/support/generate  — free-form support question
    POST /v1/support/ticket    — answer a Jira-style ticket body
    POST /v1/support/runbook   — lookup runbook steps for an incident
    GET  /v1/support/health
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("vallm.supportllm")
router = APIRouter(prefix="/v1/support", tags=["supportllm"])


class SupportQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict[str, Any]] = None
    max_new_tokens: int = Field(500, ge=16, le=2048)
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    enrich_with_web: bool = Field(
        False,
        description="If True, fetch external context (web search + scrape) and "
                    "prepend it to the prompt before generation. Used when local "
                    "docs don't have the answer.",
    )


class TicketRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1, max_length=10000)
    reporter: Optional[str] = None
    labels: Optional[List[str]] = None
    max_new_tokens: int = Field(600, ge=16, le=2048)


class RunbookRequest(BaseModel):
    incident: str = Field(..., min_length=1, max_length=2000)
    service: Optional[str] = None
    severity: Optional[str] = None
    max_new_tokens: int = Field(500, ge=16, le=2048)


def _get_backend(req: Request):
    backend = getattr(req.app.state, "supportllm", None)
    if backend is None:
        raise HTTPException(status_code=503, detail="SupportLLM backend not initialized")
    return backend


@router.get("/health")
async def health(req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    return {
        "status": "healthy" if backend.loaded else "degraded",
        "model_name": backend.cfg.display_name,
        "model_loaded": backend.loaded,
        "loaded_from": backend.loaded_from,
        "device": backend.effective_device,
        "paths": backend.describe_paths(),
    }


@router.post("/generate")
async def generate(request: SupportQueryRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()

    prompt = request.prompt
    web_meta: Optional[Dict[str, Any]] = None
    if request.enrich_with_web:
        try:
            from app.services.web import fetch_external_context
        except ImportError:
            from services.web import fetch_external_context
        web_out = await fetch_external_context(request.prompt)
        web_meta = {
            "sources": web_out.get("sources", []),
            "chars": len(web_out.get("context", "")),
            "errors": web_out.get("errors", []),
        }
        if web_out.get("context"):
            prompt = (
                "Use the following web sources to answer the user's question. "
                "Cite the URL of each fact you use.\n\n"
                f"{web_out['context']}\n\n"
                "---\n\n"
                f"User question: {request.prompt}"
            )

    result = backend.generate(
        prompt=prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        context=request.context,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    if web_meta is not None:
        result["web"] = web_meta
    return result


@router.post("/ticket")
async def ticket(request: TicketRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()
    prompt = (
        f"Ticket title: {request.title}\n"
        f"Reporter: {request.reporter or 'unknown'}\n"
        f"Labels: {', '.join(request.labels or []) or 'none'}\n\n"
        f"Ticket body:\n{request.body}\n\n"
        f"Draft a reply using the Diagnosis → Steps → Verify → Escalate format."
    )
    result = backend.generate(
        prompt=prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=0.2,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    result["title"] = request.title
    return result


@router.post("/runbook")
async def runbook(request: RunbookRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()
    prompt = (
        f"Incident: {request.incident}\n"
        f"Service: {request.service or 'unspecified'}\n"
        f"Severity: {request.severity or 'unspecified'}\n\n"
        f"Return the runbook steps using Diagnosis → Steps → Verify → Escalate."
    )
    result = backend.generate(
        prompt=prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=0.1,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    return result
