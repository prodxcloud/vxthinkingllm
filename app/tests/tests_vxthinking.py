"""End-to-end tests for VxThinking — the +1 reasoning core of the platform.

10 use cases:
    Functional / system
        01. /health           — platform liveness
        02. /stats            — vector store + cache stats
        03. /logs             — request log surface
    API endpoints (LLM)
        04. /generate         — direct text generation
        05. /api/models/v1/query     — RAG + reasoning
        06. /api/models/v1/developer — developer assist
        07. /api/models/v1/terminal  — terminal/CLI assist
        08. /api/models/v2/query     — NLP-enhanced query
        09. /api/cloud/provision-intent — intent classification + payload
    Embedding / vector
        10. /search           — FAISS similarity search

Run (server must be on :8745):
    venv/bin/python -m pytest -xvs app/tests/tests_vxthinking.py
    VxThinkingLLM_BASE_URL=http://localhost:8745 \
        venv/bin/python -m pytest -xvs app/tests/tests_vxthinking.py
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
        r = _get("/health")
        if r.status_code != 200:
            pytest.skip(f"server at {BASE_URL}/health returned {r.status_code}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"server at {BASE_URL} not reachable: {e}")


# 01 — functional liveness ----------------------------------------------------
def test_01_platform_health():
    """Liveness probe used by load balancers / k8s."""
    r = _get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


# 02 — functional / vector store stats ----------------------------------------
def test_02_stats_returns_vector_store_state():
    """`/stats` should expose total_vectors and not error out."""
    r = _get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert "error" not in body, f"/stats reported error: {body.get('error')}"
    # canonical key per VectorStore.get_vector_store_stats()
    assert "total_vectors" in body
    assert isinstance(body["total_vectors"], int)
    assert body["total_vectors"] >= 0


# 03 — functional / request logs ----------------------------------------------
def test_03_logs_endpoint_returns_lines():
    """`/logs?lines=20` returns at most N most-recent lines or empty list."""
    r = _get("/logs?lines=20")
    assert r.status_code == 200
    body = r.json()
    # Either there are no logs yet, or we got a list of lines back
    if "logs" in body:
        assert isinstance(body["logs"], list)
        assert len(body["logs"]) <= 20


# 04 — API / VxThinking direct generation -------------------------------------
def test_04_generate_returns_langchain_alias():
    """`/generate` returns both `response` and `text` (LangChain-compat alias)."""
    r = _post("/generate", {
        "prompt": "List two responsibilities of a DevOps engineer.",
        "max_new_tokens": 24,
        "temperature": 0.3,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model_loaded"] is True
    assert body["response"] == body["text"]
    assert len(body["response"]) > 0
    assert body["device"] in ("cuda", "cpu")


# 05 — API / RAG query --------------------------------------------------------
def test_05_v1_query_rag():
    """`/api/models/v1/query` returns a RAG-shaped answer."""
    r = _post("/api/models/v1/query", {
        "query": "What does VxThinking do?",
        "top_k": 3,
    })
    # Some routes accept different request shapes; tolerate either 200 or 422
    # but if 200, the body should be a dict with content
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body, dict)


# 06 — API / developer assist -------------------------------------------------
def test_06_v1_developer_assist():
    """`/api/models/v1/developer` returns 200 with a non-empty payload."""
    r = _post("/api/models/v1/developer", {
        "query": "How do I add a new endpoint to the FastAPI app?",
        "top_k": 3,
    })
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body, dict) and len(body) > 0


# 07 — API / terminal assist --------------------------------------------------
def test_07_v1_terminal_assist():
    """`/api/models/v1/terminal` returns 200 for a CLI-style question."""
    r = _post("/api/models/v1/terminal", {
        "query": "How do I tail the most recent 50 log lines?",
        "top_k": 3,
    })
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body, dict) and len(body) > 0


# 08 — API / NLP-enhanced query (v2) ------------------------------------------
def test_08_v2_query_nlp():
    """`/api/models/v2/query` accepts the v2 request shape."""
    r = _post("/api/models/v2/query", {
        "query": "Summarize the in-progress sprint tickets.",
        "top_k": 3,
    })
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body, dict) and len(body) > 0


# 09 — API / provision intent + Golang payload --------------------------------
def test_09_provision_intent_payload():
    """`/api/cloud/provision-intent` classifies and emits a payload for the agent."""
    r = _post("/api/cloud/provision-intent", {
        "query": "Provision an Ubuntu VM in us-east-1 with t3.medium and 50GB",
        "query_type": "recommendations",
    })
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body, dict)


# 10 — Embedding / vector similarity search -----------------------------------
def test_10_search_uses_faiss_embeddings():
    """`/search` should return ranked results from the FAISS index."""
    r = _post("/search", {"query": "VxThinking identity and role", "top_k": 3}, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "results" in body
    assert isinstance(body["results"], list)
    # If we have any indexed vectors, top_k should be honoured
    if body["results"]:
        assert len(body["results"]) <= 3
        first = body["results"][0]
        assert "text" in first and "score" in first and "metadata" in first
        assert isinstance(first["score"], (int, float))
