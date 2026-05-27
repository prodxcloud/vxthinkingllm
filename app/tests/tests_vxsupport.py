"""End-to-end tests for VxSupport — the IT support / docs Q&A / runbook specialist.

10 use cases:
    Functional / system
        01. /v1/support/health           — backend status + paths
        02. health.paths.dataset_dir     — points at the right slug
    API endpoints (LLM)
        03. /v1/support/generate         — free-form support question
        04. /v1/support/generate         — onboarding question
        05. /v1/support/generate         — VPN / MFA question
        06. /v1/support/ticket           — Jira-style ticket reply
        07. /v1/support/runbook          — incident runbook
    Routing / dispatcher
        08. /v1/ask     no keywords -> default routes to supportllm
        09. /v1/ask     force_model=supportllm dispatches to VxSupport
    Embedding / keyword routing
        10. /v1/ask/routes               — VxSupport keyword set is correct

Run:
    venv/bin/python -m pytest -xvs app/tests/tests_vxsupport.py
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
        r = _get("/v1/support/health")
        if r.status_code != 200:
            pytest.skip(f"server at {BASE_URL}/v1/support/health returned {r.status_code}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"server at {BASE_URL} not reachable: {e}")


# 01 — functional health ------------------------------------------------------
def test_01_health_loaded():
    """`/v1/support/health` reports healthy with weights loaded."""
    r = _get("/v1/support/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy", f"VxSupport degraded: {body}"
    assert body["model_loaded"] is True
    assert body["model_name"] == "VxSupport v1.0"
    assert "/supportllm" in body["loaded_from"]


# 02 — functional / paths point at the right slug ----------------------------
def test_02_health_paths_point_to_supportllm_slug():
    """Health response exposes resolved paths and they reference supportllm."""
    r = _get("/v1/support/health")
    paths = r.json()["paths"]
    assert "/supportllm" in paths["model_path"]
    assert "/supportllm" in paths.get("dataset_dir", "")
    assert paths.get("prefix") == "/v1/support"


# 03 — API / free-form support question --------------------------------------
def test_03_generate_support_question():
    """Generic support question succeeds."""
    r = _post("/v1/support/generate", {
        "prompt": "How do I reset my MFA device on the developer portal?",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("model_loaded") is True
    assert isinstance(body.get("response"), str) and len(body["response"]) > 0
    assert "duration_ms" in body


# 04 — API / onboarding question ---------------------------------------------
def test_04_generate_onboarding():
    """Onboarding-flavoured prompt succeeds."""
    r = _post("/v1/support/generate", {
        "prompt": "What's the day-1 onboarding checklist for a new engineer?",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json().get("response"), str)


# 05 — API / VPN / access question -------------------------------------------
def test_05_generate_vpn_access():
    """Network/access support prompt succeeds."""
    r = _post("/v1/support/generate", {
        "prompt": "I cannot connect to the corporate VPN — how do I troubleshoot?",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json().get("response"), str)


# 06 — API / Jira-style ticket reply -----------------------------------------
def test_06_ticket_reply_diagnosis_format():
    """`/v1/support/ticket` accepts the ticket payload and echoes the title."""
    r = _post("/v1/support/ticket", {
        "title": "Container is OOMKilled every 2h",
        "body": "Production pod fastapi-svc-7c8 is restarting with OOMKilled. Logs show 4Gi RSS at peak.",
        "reporter": "alice",
        "labels": ["incident", "production"],
        "max_new_tokens": 24,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("response"), str) and len(body["response"]) > 0
    assert body.get("title") == "Container is OOMKilled every 2h"
    assert "duration_ms" in body


# 07 — API / runbook lookup ---------------------------------------------------
def test_07_runbook_for_incident():
    """`/v1/support/runbook` accepts an incident description."""
    r = _post("/v1/support/runbook", {
        "incident": "Kubernetes pods stuck in CrashLoopBackOff after deployment",
        "service": "fastapi-svc",
        "severity": "high",
        "max_new_tokens": 24,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("response"), str) and len(body["response"]) > 0
    assert "duration_ms" in body


# 08 — Routing / default-when-no-match is supportllm -------------------------
def test_08_universal_default_route_is_supportllm():
    """`/v1/ask` with a prompt that matches no keywords defaults to supportllm."""
    r = _post("/v1/ask", {
        "prompt": "xyz random unmatched text 12345",
        "max_new_tokens": 16,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    # routing_scores should all be 0 -> falls back to supportllm
    assert body["routed_to"] == "supportllm"


# 09 — Routing / explicit force_model ----------------------------------------
def test_09_universal_dispatcher_routes_to_supportllm():
    """`/v1/ask` with force_model=supportllm reaches VxSupport."""
    r = _post("/v1/ask", {
        "prompt": "Where can I find onboarding docs?",
        "force_model": "supportllm",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "supportllm"
    assert "routing_scores" in body
    assert isinstance(body["response"], str)


# 10 — Embedding / keyword routing table -------------------------------------
def test_10_routing_table_has_vxsupport_keywords():
    """`/v1/ask/routes` exposes the supportllm keyword set + default fallback."""
    r = _get("/v1/ask/routes")
    assert r.status_code == 200
    body = r.json()
    assert body["default_when_no_match"] == "supportllm"
    support_kw = set(body["routing_rules"]["supportllm"])
    for kw in ("how to", "error", "support", "docs", "troubleshoot", "mfa", "onboarding"):
        assert kw in support_kw, f"missing VxSupport keyword: {kw}"
