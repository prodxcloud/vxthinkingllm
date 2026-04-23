"""
VxCoder routes — /v1/coding

Exposes:
    POST /v1/coding/generate
    POST /v1/coding/edit
    POST /v1/coding/review
    GET  /v1/coding/health
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("vallm.codingllm")
router = APIRouter(prefix="/v1/coding", tags=["codingllm"])


class CodeGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    language: Optional[str] = Field(None, description="python|typescript|go|rust|...")
    framework: Optional[str] = Field(None, description="fastapi|react|nextjs|...")
    context: Optional[Dict[str, Any]] = None
    max_new_tokens: int = Field(800, ge=16, le=4096)
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)


class CodeEditRequest(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=4000)
    files: List[Dict[str, str]] = Field(
        ..., description="[{'path': 'a.py', 'content': '...'}, ...]"
    )
    language: Optional[str] = None
    max_new_tokens: int = Field(1200, ge=16, le=4096)
    temperature: float = Field(0.2, ge=0.0, le=2.0)


class CodeReviewRequest(BaseModel):
    diff: str = Field(..., min_length=1, max_length=20000)
    focus: Optional[str] = Field("correctness,security,readability")
    max_new_tokens: int = Field(600, ge=16, le=4096)


def _get_backend(req: Request):
    backend = getattr(req.app.state, "codingllm", None)
    if backend is None:
        raise HTTPException(status_code=503, detail="CodingLLM backend not initialized")
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
async def generate(request: CodeGenerateRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()
    context = dict(request.context or {})
    if request.language:
        context["language"] = request.language
    if request.framework:
        context["framework"] = request.framework

    result = backend.generate(
        prompt=request.prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        context=context or None,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    return result


@router.post("/edit")
async def edit(request: CodeEditRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()
    files_block = "\n\n".join(
        f"### File: {f.get('path','?')}\n```\n{f.get('content','')}\n```" for f in request.files
    )
    prompt = (
        f"{request.instruction}\n\n"
        f"Apply your edits as XML search/replace diffs per file.\n\n"
        f"{files_block}"
    )
    result = backend.generate(
        prompt=prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        context={"language": request.language} if request.language else None,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    result["files_in"] = [f.get("path") for f in request.files]
    return result


@router.post("/review")
async def review(request: CodeReviewRequest, req: Request) -> Dict[str, Any]:
    backend = _get_backend(req)
    start = time.perf_counter()
    prompt = (
        f"Review the following diff. Focus areas: {request.focus}.\n"
        f"For each issue: file:line — severity — explanation — suggested fix.\n\n"
        f"```diff\n{request.diff}\n```"
    )
    result = backend.generate(
        prompt=prompt,
        max_new_tokens=request.max_new_tokens,
        temperature=0.1,
    )
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    return result
