"""
VxCloud LLM Service
===================
Single-purpose FastAPI app that serves the VxCloud specialist LLM.

There is no database, no ORM, no schemas, no request/response persistence,
and no other LLM backends. Requests are processed in memory and discarded;
nothing about a call is written to disk.

Endpoints:
    GET  /             - landing page
    GET  /health       - liveness check
    POST /v1/cloud/generate
    POST /v1/cloud/query
    GET  /v1/cloud/health
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is on sys.path so `app.*` imports resolve when run as `python app/app.py`.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

try:
    from .services.ai.ml import CloudLLMBackend, build_cloudllm_config, cloudllm_router
except ImportError:
    from services.ai.ml import CloudLLMBackend, build_cloudllm_config, cloudllm_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    backend = CloudLLMBackend(build_cloudllm_config(device=device))
    backend.load()
    app.state.cloudllm = backend
    yield


app = FastAPI(
    title="VxCloud LLM",
    description="Single cloud-LLM service. No database, no logging, no persistence.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cloudllm_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(
        """<!doctype html>
<html><head><meta charset="utf-8"><title>VxCloud LLM</title>
<style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;padding:48px;max-width:720px;margin:0 auto}
code{background:#1e293b;padding:2px 6px;border-radius:4px}a{color:#7dd3fc}</style></head>
<body><h1>VxCloud LLM</h1>
<p>Single cloud-LLM service. No database, no persistence.</p>
<ul>
  <li><code>GET  /health</code></li>
  <li><code>GET  /v1/cloud/health</code></li>
  <li><code>POST /v1/cloud/generate</code></li>
  <li><code>POST /v1/cloud/query</code></li>
  <li><a href="/docs">/docs</a> &middot; <a href="/redoc">/redoc</a></li>
</ul></body></html>"""
    )


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, Exception):
            pass

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8745")), reload=False)
