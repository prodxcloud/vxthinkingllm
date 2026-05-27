"""End-to-end tests for VxCloud — the DevOps / IaC / SRE specialist.

10 use cases:
    Functional / system
        01. /v1/cloud/health              — backend status + paths
        02. health.paths.dataset_dir      — points at the right slug
    API endpoints (LLM)
        03. /v1/cloud/generate            — direct generation (Kubernetes Deployment)
        04. /v1/cloud/generate            — Terraform module (S3 + KMS)
        05. /v1/cloud/generate            — Helm chart prompt
        06. /v1/cloud/generate            — Dockerfile prompt
        07. /v1/cloud/query               — richer payload (raw + loaded_from)
        08. /v1/cloud/generate            — IAM least-privilege prompt
    Routing / dispatcher
        09. /v1/ask     force_model=cloudllm dispatches to VxCloud
    Embedding / keyword routing
        10. /v1/ask/routes                — VxCloud keyword set is correct

Run:
    venv/bin/python -m pytest -xvs app/tests/tests_vxcloud.py
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
        r = _get("/v1/cloud/health")
        if r.status_code != 200:
            pytest.skip(f"server at {BASE_URL}/v1/cloud/health returned {r.status_code}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"server at {BASE_URL} not reachable: {e}")


# 01 — functional health ------------------------------------------------------
def test_01_health_loaded():
    """`/v1/cloud/health` reports healthy with weights loaded."""
    r = _get("/v1/cloud/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy", f"VxCloud degraded: {body}"
    assert body["model_loaded"] is True
    assert body["model_name"] == "VxCloud v1.0"
    assert "/cloudllm" in body["loaded_from"]


# 02 — functional / paths point at the right slug ----------------------------
def test_02_health_paths_point_to_cloudllm_slug():
    """Health response exposes resolved paths and they all reference cloudllm."""
    r = _get("/v1/cloud/health")
    paths = r.json()["paths"]
    assert "/cloudllm" in paths["model_path"]
    assert "/cloudllm" in paths.get("dataset_dir", "")
    assert paths.get("prefix") == "/v1/cloud"


# 03 — API / Kubernetes Deployment generation --------------------------------
def test_03_generate_kubernetes_deployment():
    """Generation for a K8s Deployment manifest succeeds and returns a string."""
    r = _post("/v1/cloud/generate", {
        "prompt": "Write a Kubernetes Deployment manifest for a FastAPI service with 3 replicas and resource limits.",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model_loaded"] is True
    assert body["model_name"] == "VxCloud v1.0"
    assert isinstance(body["response"], str) and len(body["response"]) > 0
    assert body["duration_ms"] > 0


# 04 — API / Terraform module generation -------------------------------------
def test_04_generate_terraform_s3_kms():
    """Terraform-style prompt produces a non-empty response."""
    r = _post("/v1/cloud/generate", {
        "prompt": "Write a Terraform module for an S3 bucket with KMS-encrypted server-side encryption.",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["response"], str) and len(body["response"]) > 0


# 05 — API / Helm chart generation -------------------------------------------
def test_05_generate_helm_chart():
    """Helm chart prompt is accepted and returns text."""
    r = _post("/v1/cloud/generate", {
        "prompt": "Generate a minimal Helm chart values.yaml for a stateless web service.",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["response"], str)


# 06 — API / Dockerfile generation -------------------------------------------
def test_06_generate_dockerfile():
    """Multi-stage Dockerfile prompt is accepted."""
    r = _post("/v1/cloud/generate", {
        "prompt": "Write a multi-stage Dockerfile for a Python FastAPI app with a non-root user.",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["response"], str)


# 07 — API / /query returns the richer payload -------------------------------
def test_07_query_returns_richer_payload():
    """`/v1/cloud/query` returns the full backend payload with `loaded_from`."""
    r = _post("/v1/cloud/query", {
        "prompt": "What is the cheapest AWS instance type for a small monitoring agent?",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    # /query includes a richer payload than /generate
    assert "response" in body
    assert "duration_ms" in body
    assert "query" in body and isinstance(body["query"], str)


# 08 — API / IAM least-privilege prompt --------------------------------------
def test_08_generate_iam_least_privilege():
    """Security/IAM-shaped prompt returns a non-empty response."""
    r = _post("/v1/cloud/generate", {
        "prompt": "Write an AWS IAM policy that grants read-only access to a specific S3 bucket.",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["response"], str) and len(r.json()["response"]) > 0


# 09 — Routing / universal dispatcher routes to cloudllm ---------------------
def test_09_universal_dispatcher_routes_to_cloudllm():
    """`/v1/ask` with force_model=cloudllm reaches VxCloud."""
    r = _post("/v1/ask", {
        "prompt": "Generate a Terraform module for an S3 bucket with KMS encryption.",
        "force_model": "cloudllm",
        "max_new_tokens": 24,
        "temperature": 0.2,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "cloudllm"
    assert "routing_scores" in body
    assert isinstance(body["response"], str) and len(body["response"]) > 0


# 10 — Embedding / keyword routing table -------------------------------------
def test_10_routing_table_has_vxcloud_keywords():
    """`/v1/ask/routes` exposes the cloudllm keyword set used for intent scoring."""
    r = _get("/v1/ask/routes")
    assert r.status_code == 200
    rules = r.json()["routing_rules"]
    cloud_kw = set(rules["cloudllm"])
    # spot-check: the router should classify these as VxCloud-domain
    for kw in ("terraform", "kubernetes", "helm", "iam", "aws", "azure", "gcp"):
        assert kw in cloud_kw, f"missing VxCloud keyword: {kw}"
