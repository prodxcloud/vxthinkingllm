"""
VxCloud LLM routes.

All inference endpoints hit the same in-process CloudLLM backend:

    POST /generate           — primary generation
    POST /execute            — alias for /generate
    POST /run                — alias for /generate
    POST /v1/model/generate  — namespaced alias for /generate
    POST /v1/model/query     — generation + richer payload (raw, loaded_from, ...)
    GET  /v1/model/health    — backend status
"""

import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("vxcloud")
router = APIRouter(tags=["cloudllm"])


class CloudGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    max_new_tokens: int = Field(400, ge=16, le=2048)
    temperature: float = Field(0.3, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    context: Optional[Dict[str, Any]] = None


class CloudGenerateResponse(BaseModel):
    response: str
    model_loaded: bool
    device: str
    model_name: str
    duration_ms: float


def _get_backend(req: Request):
    backend = getattr(req.app.state, "cloudllm", None)
    if backend is None:
        raise HTTPException(status_code=503, detail="CloudLLM backend not initialized")
    return backend


def _run_generate(request: CloudGenerateRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()
    result = backend.generate(
        prompt=request.prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        context=request.context,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    return result


@router.get("/v1/model/health")
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


@router.post("/generate", response_model=CloudGenerateResponse)
@router.post("/execute", response_model=CloudGenerateResponse)
@router.post("/run", response_model=CloudGenerateResponse)
@router.post("/v1/model/generate", response_model=CloudGenerateResponse)
async def generate(request: CloudGenerateRequest, req: Request) -> CloudGenerateResponse:
    result = _run_generate(request, req)
    return CloudGenerateResponse(
        response=str(result.get("response", "")),
        model_loaded=bool(result.get("model_loaded")),
        device=str(result.get("device", "none")),
        model_name=str(result.get("model_name", "VxCloud v1.0")),
        duration_ms=float(result.get("duration_ms", 0.0)),
    )


@router.post("/v1/model/query")
async def query(request: CloudGenerateRequest, req: Request) -> Dict[str, Any]:
    """Generate + return the richer payload (raw, loaded_from, etc.)."""
    result = _run_generate(request, req)
    result["query"] = request.prompt
    return result
