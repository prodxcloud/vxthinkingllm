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


# Where the "Back to Dashboard" control points. This service runs standalone on
# :8745, so it cannot resolve the web app's origin on its own.
DASHBOARD_URL = os.getenv("VXCLOUD_DASHBOARD_URL", "https://vxcloud.io/dashboard")

# Theme contract mirrors vxcloud_web's ThemeContext: localStorage key "theme"
# holding "light" | "dark" | "system", defaulting to "system". The dashboard is a
# different origin, so the preference cannot be shared with it — this page keeps
# its own copy under the same key and semantics.
_LANDING_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VxCloud LLM</title>
<script>
  // Applied before first paint so a dark-mode user never sees a white flash.
  (function () {
    try {
      var t = localStorage.getItem('theme') || 'system';
      if (t === 'light' || t === 'dark') {
        document.documentElement.setAttribute('data-theme', t);
      }
    } catch (e) {}
  })();
</script>
<style>
  :root {
    --bg: #ffffff; --fg: #0f172a; --muted: #64748b;
    --card: #f8fafc; --border: #e2e8f0; --accent: #0369a1;
    --code-bg: #f1f5f9; --code-fg: #0f172a;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f172a; --fg: #e2e8f0; --muted: #94a3b8;
      --card: #1e293b; --border: #334155; --accent: #7dd3fc;
      --code-bg: #1e293b; --code-fg: #e2e8f0;
    }
  }
  /* Explicit choice must win over the OS preference in BOTH directions. */
  :root[data-theme="light"] {
    --bg: #ffffff; --fg: #0f172a; --muted: #64748b;
    --card: #f8fafc; --border: #e2e8f0; --accent: #0369a1;
    --code-bg: #f1f5f9; --code-fg: #0f172a;
  }
  :root[data-theme="dark"] {
    --bg: #0f172a; --fg: #e2e8f0; --muted: #94a3b8;
    --card: #1e293b; --border: #334155; --accent: #7dd3fc;
    --code-bg: #1e293b; --code-fg: #e2e8f0;
  }
  * { box-sizing: border-box; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--fg);
    margin: 0; padding: 0 24px 64px;
    transition: background .15s ease, color .15s ease;
  }
  header {
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
    max-width: 760px; margin: 0 auto; padding: 20px 0;
    border-bottom: 1px solid var(--border);
  }
  .brand { font-weight: 700; letter-spacing: -.01em; }
  .actions { display: flex; align-items: center; gap: 8px; }
  .btn {
    display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid var(--border); background: var(--card); color: var(--fg);
    border-radius: 8px; padding: 7px 12px; font: inherit; font-size: 14px;
    cursor: pointer; text-decoration: none; line-height: 1;
  }
  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .icon-btn { padding: 7px 9px; }
  main { max-width: 760px; margin: 0 auto; }
  h1 { margin: 32px 0 8px; font-size: 28px; letter-spacing: -.02em; }
  .sub { color: var(--muted); margin: 0 0 28px; }
  ul { list-style: none; padding: 0; margin: 0; }
  li {
    border: 1px solid var(--border); background: var(--card);
    border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
  }
  code {
    background: var(--code-bg); color: var(--code-fg);
    padding: 2px 6px; border-radius: 4px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
  }
  a { color: var(--accent); }
  .method { display: inline-block; min-width: 44px; font-weight: 700; font-size: 12px; color: var(--muted); }
</style>
</head>
<body>
<header>
  <span class="brand">VxCloud LLM</span>
  <div class="actions">
    <a class="btn" href="__DASHBOARD_URL__">&larr; Back to Dashboard</a>
    <button class="btn icon-btn" id="theme-toggle" type="button"
            aria-label="Toggle light and dark mode" title="Toggle light / dark">
      <span id="theme-icon" aria-hidden="true">&#9788;</span>
    </button>
  </div>
</header>

<main>
  <h1>VxCloud LLM</h1>
  <p class="sub">Single cloud-LLM service. No database, no persistence.</p>
  <ul>
    <li><span class="method">GET</span> <code>/health</code></li>
    <li><span class="method">GET</span> <code>/v1/cloud/health</code></li>
    <li><span class="method">POST</span> <code>/v1/cloud/generate</code></li>
    <li><span class="method">POST</span> <code>/v1/cloud/query</code></li>
    <li><span class="method">DOCS</span> <a href="/docs">/docs</a> &middot; <a href="/redoc">/redoc</a></li>
  </ul>
</main>

<script>
  (function () {
    var root = document.documentElement;
    var btn = document.getElementById('theme-toggle');
    var icon = document.getElementById('theme-icon');
    var mq = window.matchMedia('(prefers-color-scheme: dark)');

    function stored() {
      try { return localStorage.getItem('theme') || 'system'; } catch (e) { return 'system'; }
    }
    function isDark() {
      var t = stored();
      return t === 'dark' || (t === 'system' && mq.matches);
    }
    function paint() {
      // Sun while dark (click for light), moon while light (click for dark).
      icon.innerHTML = isDark() ? '&#9788;' : '&#9789;';
    }
    btn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      try { localStorage.setItem('theme', next); } catch (e) {}
      root.setAttribute('data-theme', next);
      paint();
    });
    // Track the OS only while the user hasn't made an explicit choice.
    mq.addEventListener('change', function () { if (stored() === 'system') paint(); });
    paint();
  })();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(_LANDING_PAGE.replace("__DASHBOARD_URL__", DASHBOARD_URL))


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
