"""End-to-end tests for VxCoder — the code-gen / multi-file edit / PR review specialist.

10 use cases:
    Functional / system
        01. /v1/coding/health           — backend status + paths
        02. health.paths.dataset_dir    — points at the right slug
    API endpoints (LLM)
        03. /v1/coding/generate         — Python function
        04. /v1/coding/generate         — TypeScript / React component
        05. /v1/coding/generate         — FastAPI endpoint
        06. /v1/coding/generate         — Go function
        07. /v1/coding/edit             — multi-file edit accepts XML diff shape
        08. /v1/coding/review           — diff review with focus
    Routing / dispatcher
        09. /v1/ask     force_model=codingllm dispatches to VxCoder
    Embedding / keyword routing
        10. /v1/ask/routes              — VxCoder keyword set is correct

Run:
    venv/bin/python -m pytest -xvs app/tests/tests_vxcoder.py
"""

from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get("VxThinkingLLM_BASE_URL", "http://localhost:8745").rstrip("/")
GEN_TIMEOUT = float(os.environ.get("VxThinkingLLM_GEN_TIMEOUT", "300"))
HEALTH_TIMEOUT = 10


def _get(path: str, *, timeout: float = HEALTH_TIMEOUT) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=timeout)


def _post(path: str, body: dict, *, timeout: float = GEN_TIMEOUT) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", json=body, timeout=timeout)


@pytest.fixture(scope="module", autouse=True)
def _server_must_be_up():
    try:
        r = _get("/v1/coding/health")
        if r.status_code != 200:
            pytest.skip(f"server at {BASE_URL}/v1/coding/health returned {r.status_code}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"server at {BASE_URL} not reachable: {e}")


# 01 — functional health ------------------------------------------------------
def test_01_health_loaded():
    """`/v1/coding/health` reports healthy with weights loaded."""
    r = _get("/v1/coding/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy", f"VxCoder degraded: {body}"
    assert body["model_loaded"] is True
    assert body["model_name"] == "VxCoder v1.0"
    assert "/codingllm" in body["loaded_from"]


# 02 — functional / paths point at the right slug ----------------------------
def test_02_health_paths_point_to_codingllm_slug():
    """Health response exposes resolved paths and they reference codingllm."""
    r = _get("/v1/coding/health")
    paths = r.json()["paths"]
    assert "/codingllm" in paths["model_path"]
    assert "/codingllm" in paths.get("dataset_dir", "")
    assert paths.get("prefix") == "/v1/coding"


# 03 — API / Python generation -----------------------------------------------
def test_03_generate_python_function():
    """Python code generation accepts language hint and returns text."""
    r = _post("/v1/coding/generate", {
        "prompt": "Write a Python function flatten(d) that flattens a nested dict using dot keys.",
        "language": "python",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("model_loaded") is True
    assert isinstance(body.get("response"), str) and len(body["response"]) > 0
    assert "duration_ms" in body


# 04 — API / TypeScript / React component ------------------------------------
def test_04_generate_react_component():
    """Frontend-flavoured prompt with framework hint succeeds."""
    r = _post("/v1/coding/generate", {
        "prompt": "Write a React functional component <UserCard name email /> with TypeScript types.",
        "language": "typescript",
        "framework": "react",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["response"], str)


# 05 — API / FastAPI endpoint -------------------------------------------------
def test_05_generate_fastapi_endpoint():
    """Backend-flavoured prompt with framework hint succeeds."""
    r = _post("/v1/coding/generate", {
        "prompt": "Add a POST /healthz endpoint to a FastAPI app that returns {'status': 'ok'}.",
        "language": "python",
        "framework": "fastapi",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["response"], str)


# 06 — API / Go function ------------------------------------------------------
def test_06_generate_go_function():
    """Go code generation succeeds."""
    r = _post("/v1/coding/generate", {
        "prompt": "Write a Go function ReverseString(s string) string.",
        "language": "go",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["response"], str)


# 07 — API / multi-file edit returns expected envelope -----------------------
def test_07_edit_accepts_files_payload():
    """`/v1/coding/edit` accepts the multi-file payload and echoes the file list."""
    r = _post("/v1/coding/edit", {
        "instruction": "Rename greet() to say_hello() in the file below.",
        "files": [{"path": "greet.py", "content": "def greet(name):\n    return f'Hi {name}'"}],
        "language": "python",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("response"), str)
    assert body.get("files_in") == ["greet.py"]
    assert "duration_ms" in body


# 08 — API / PR review on a diff ---------------------------------------------
def test_08_review_diff_with_focus():
    """`/v1/coding/review` accepts a diff and a focus list."""
    diff = (
        "--- a/src/api.py\n"
        "+++ b/src/api.py\n"
        "@@ -1,4 +1,4 @@\n"
        "-def add(a, b):\n"
        "-    return a + b\n"
        "+def add(a: int, b: int) -> int:\n"
        "+    return a + b\n"
    )
    r = _post("/v1/coding/review", {
        "diff": diff,
        "focus": "correctness,security,readability",
        "max_new_tokens": 24,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("response"), str) and len(body["response"]) > 0
    assert "duration_ms" in body


# 09 — Routing / universal dispatcher routes to codingllm --------------------
def test_09_universal_dispatcher_routes_to_codingllm():
    """`/v1/ask` with force_model=codingllm reaches VxCoder."""
    r = _post("/v1/ask", {
        "prompt": "Refactor this function to use early returns.",
        "force_model": "codingllm",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "codingllm"
    assert "routing_scores" in body
    assert isinstance(body["response"], str)


# 10 — Embedding / keyword routing table -------------------------------------
def test_10_routing_table_has_vxcoder_keywords():
    """`/v1/ask/routes` exposes the codingllm keyword set used for intent scoring."""
    r = _get("/v1/ask/routes")
    assert r.status_code == 200
    rules = r.json()["routing_rules"]
    coder_kw = set(rules["codingllm"])
    for kw in ("code", "function", "class", "refactor", "test", "review", "python", "typescript"):
        assert kw in coder_kw, f"missing VxCoder keyword: {kw}"
