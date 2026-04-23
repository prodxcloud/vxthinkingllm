"""
Universal router — /v1/ask

Single entry point that classifies intent (keyword-based, no ML) and dispatches
to the appropriate specialist backend:

    thinkingllm — planning, tickets, sprints, predictions, forecasts
    cloudllm    — DevOps, IaC, Kubernetes, runbooks, cost
    codingllm   — code generation, edits, reviews, tests
    supportllm  — IT support, docs Q&A, troubleshooting

The classifier is a ranked keyword match; `supportllm` is the default when no
keyword scores.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("vallm.universal")
router = APIRouter(prefix="/v1", tags=["universal"])


# Order in this dict is the tiebreak order when scores tie
ROUTING_RULES: Dict[str, list[str]] = {
    "cloudllm": [
        "terraform", "kubernetes", "k8s", "ansible", "helm",
        "yaml", "deploy", "infrastructure", "iac", "eks", "aks", "gke",
        "incident", "runbook", "cost", "vpc", "subnet", "nginx",
        "dockerfile", "pipeline", "ci/cd", "cicd", "cloud",
        "aws", "azure", "gcp", "iam", "s3", "ec2", "lambda",
        "sre", "observability", "prometheus", "grafana",
    ],
    "codingllm": [
        "code", "function", "class", "refactor", "bug", "fix",
        "test", "write", "implement", "vibe", "generate", "review",
        "pr", "pull request", "python", "javascript", "typescript",
        "react", "fastapi", "api", "endpoint", "module",
        "diff", "patch", "unit test", "integration test",
    ],
    "supportllm": [
        "how do i", "how to", "error", "issue", "support",
        "docs", "documentation", "runbook", "troubleshoot",
        "access", "permission", "install", "configure", "setup",
        "jira", "confluence", "notion", "slack", "ticket",
        "password", "vpn", "mfa", "onboarding",
    ],
    "thinkingllm": [
        "ticket", "sprint", "predict", "backlog", "estimate",
        "jira", "story points", "blocker", "dependency",
        "planning", "next", "forecast", "anomaly",
        "roadmap", "plan",
    ],
}


# Overlap between thinkingllm (planning) and supportllm (ticket/jira) is
# intentional — a tie breaks toward the first dict key in ROUTING_RULES.


def classify_intent(prompt: str) -> Tuple[str, Dict[str, int]]:
    """Return (chosen_model, score_breakdown).

    Defaults to `supportllm` when nothing matches.
    """
    p = (prompt or "").lower()
    scores = {m: 0 for m in ROUTING_RULES}
    for model, keywords in ROUTING_RULES.items():
        for kw in keywords:
            if kw in p:
                scores[model] += 1

    # highest score wins; ties resolved by ROUTING_RULES insertion order
    best_model = max(scores, key=lambda m: (scores[m], -list(ROUTING_RULES).index(m)))
    if scores[best_model] == 0:
        best_model = "supportllm"
    return best_model, scores


class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    context: Optional[Dict[str, Any]] = None
    max_new_tokens: int = Field(500, ge=16, le=2048)
    temperature: float = Field(0.3, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    force_model: Optional[str] = Field(
        None,
        description="Override routing: one of thinkingllm|cloudllm|codingllm|supportllm",
    )


def _dispatch_thinkingllm(req: Request, payload: AskRequest) -> Dict[str, Any]:
    """Call the existing VxThinkingLLM /generate handler in-process.

    VxThinkingLLM doesn't use the SpecialistBackend wrapper — its model /
    tokenizer live directly on app.state (see app/app.py lifespan). We mirror
    the exact call pattern from app/app.py:/generate here.
    """
    import torch
    tokenizer = getattr(req.app.state, "tokenizer", None)
    model = getattr(req.app.state, "model", None)
    if tokenizer is None or model is None:
        return {
            "response": "VxThinkingLLM not loaded. Run: python -m app.services.ai.ml.train",
            "model_loaded": False,
            "device": "none",
            "model_name": "VxThinking v1.2",
        }

    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = tokenizer(payload.prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    text = tokenizer.decode(output[0], skip_special_tokens=True)
    return {
        "response": text,
        "model_loaded": True,
        "device": device,
        "model_name": "VxThinking v1.2",
    }


def _dispatch_specialist(req: Request, slug: str, payload: AskRequest) -> Dict[str, Any]:
    backend = getattr(req.app.state, slug, None)
    if backend is None:
        raise HTTPException(
            status_code=503,
            detail=f"{slug} backend not initialized",
        )
    return backend.generate(
        prompt=payload.prompt,
        max_new_tokens=payload.max_new_tokens,
        temperature=payload.temperature,
        top_p=payload.top_p,
        context=payload.context,
    )


@router.post("/ask")
async def ask(request: AskRequest, req: Request) -> Dict[str, Any]:
    """Universal single endpoint. Classifies and dispatches."""
    start = time.perf_counter()

    if request.force_model:
        chosen = request.force_model.lower().strip()
        if chosen not in {"thinkingllm", "cloudllm", "codingllm", "supportllm"}:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid force_model '{chosen}'. Must be one of "
                       "thinkingllm|cloudllm|codingllm|supportllm.",
            )
        scores = {chosen: 99}
    else:
        chosen, scores = classify_intent(request.prompt)

    logger.info("universal /ask | routed_to=%s scores=%s", chosen, scores)

    if chosen == "thinkingllm":
        result = _dispatch_thinkingllm(req, request)
    else:
        result = _dispatch_specialist(req, chosen, request)

    result["routed_to"] = chosen
    result["routing_scores"] = scores
    result["duration_ms"] = (time.perf_counter() - start) * 1000
    return result


@router.get("/ask/routes")
async def routes_info() -> Dict[str, Any]:
    """Inspect the routing table + available models."""
    return {
        "routing_rules": {m: kws for m, kws in ROUTING_RULES.items()},
        "default_when_no_match": "supportllm",
        "available_models": list(ROUTING_RULES.keys()),
    }
