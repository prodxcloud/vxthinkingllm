"""
VaLLM Regression Test Suite - Comprehensive System Tests
=========================================================

Author: Joel Otepa Wembo
https://joelwembo.com

DESCRIPTION
===========
Self-contained regression test suite that validates every major endpoint and
ML function in the VaLLM cloud operations AI pipeline.  Tests are split into
three groups:

    API Tests   (14 tests) - Hit the live FastAPI server at http://localhost:8746
    Unit Tests  (5 tests)  - Call ML services directly (no server needed)
    Interactive mode       - Chat with the VaLLM system in your terminal

Each test is scored 1-10 for quality/accuracy:
    10  = Perfect - all checks pass with excellent metrics
    7-9 = Good   - functional with minor gaps
    4-6 = Fair   - works but significant quality issues
    1-3 = Poor   - critical failures or missing functionality

PREREQUISITES
=============
    pip install pytest pytest-asyncio httpx requests numpy

USAGE
=====
    # Start the app first:
    uvicorn app.app:app --host 0.0.0.0 --port 8746

    # Run ALL tests (server must be running for API tests)
    pytest app/tests/tests.py -v -s

    # Run only API tests
    pytest app/tests/tests.py -v -s -k "api"

    # Run only unit tests (no server needed)
    pytest app/tests/tests.py -v -s -k "unit"

    # Run interactive chat
    python -m app.tests.tests --interactive

    # Run batch regression tests
    python -m app.tests.tests

    # Custom URL
    python -m app.tests.tests --url http://localhost:8746

API ENDPOINTS TESTED
====================
    Core:
        GET  /health                          Health check
        GET  /stats                           Vector store stats
        GET  /logs                            Recent logs
        POST /search                          Vector similarity search
        POST /generate                        LLM text generation

    V1 (RAG + Reasoning):
        POST /api/models/v1/query             RAG query with reasoning
        POST /api/models/v1/developer         Developer assistance
        POST /api/models/v1/terminal          Terminal/CLI assistance

    V2 (NLP + Document Analysis):
        POST /api/models/v2/query             NLP-enhanced query
        POST /api/models/v2/extract           Entity extraction
        GET  /api/models/v2/status            NLP capabilities

    V3 (Incident Patterns):
        POST /api/models/v3/query             Unusual incident patterns

    Cloud Provisioning (Intent Detection):
        POST /api/cloud/provision-intent      Intent + Golang payload
             Detects deployment/provisioning intents and extracts
             parameters.  Not for monitoring or status checks.

UNIT FUNCTIONS TESTED
=====================
    EntityExtractor.extract_entities     - Cloud entity extraction
    VectorStore.search                   - FAISS semantic search
    ReasoningEngine.reason               - Chain-of-thought reasoning
    Provision intent classification      - Query type routing
    LLM generation (if model loaded)     - Text generation quality
"""

import asyncio
import atexit
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_APP_DIR = _PROJECT_ROOT / "app"
for _p in [str(_PROJECT_ROOT), str(_APP_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Attempt to import httpx; fall back to requests
# ---------------------------------------------------------------------------
try:
    import httpx
except ImportError:
    httpx = None

import requests as _requests_lib

# ---------------------------------------------------------------------------
# Base URL
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("VALLM_TEST_URL", "http://localhost:8746")

# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------
_SCORECARD: Dict[str, Dict[str, Any]] = {}
_TEST_COUNTER = 0


def _record_score(test_name: str, score: int, details: str = ""):
    global _TEST_COUNTER
    _TEST_COUNTER += 1
    score = max(1, min(10, score))
    bar = "#" * score + "." * (10 - score)
    label = (
        "PERFECT" if score == 10 else
        "EXCELLENT" if score >= 8 else
        "GOOD" if score >= 6 else
        "FAIR" if score >= 4 else
        "POOR"
    )
    _SCORECARD[f"Test {_TEST_COUNTER}"] = {
        "name": test_name, "score": score, "label": label, "details": details,
    }
    print(f"\n  {'=' * 65}")
    print(f"  [Test {_TEST_COUNTER}] {test_name}")
    print(f"  Score: {score}/10 [{bar}] {label}")
    if details:
        print(f"  Details: {details}")
    print(f"  {'=' * 65}")


def _print_final_scorecard():
    if not _SCORECARD:
        return
    total = sum(v["score"] for v in _SCORECARD.values())
    count = len(_SCORECARD)
    avg = total / count if count else 0
    print("\n\n" + "=" * 70)
    print("  VALLM REGRESSION TEST SUITE - FINAL SCORECARD")
    print("=" * 70)
    for key, val in _SCORECARD.items():
        bar = "#" * val["score"] + "." * (10 - val["score"])
        print(f"  {key:>8} | {val['score']:>2}/10 [{bar}] {val['label']:<10} | {val['name']}")
    print("-" * 70)
    print(f"  {'TOTAL':>8} | {total}/{count * 10}  Average: {avg:.1f}/10")
    overall = (
        "EXCELLENT" if avg >= 8 else "GOOD" if avg >= 6 else
        "NEEDS IMPROVEMENT" if avg >= 4 else "CRITICAL ISSUES"
    )
    print(f"  Overall Assessment: {overall}")
    print("=" * 70)


atexit.register(_print_final_scorecard)


# ============================================================================
# SAMPLE DATA - Provisioning queries modelled on cloud_deployments.csv
# ============================================================================

PROVISION_TESTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Provision VM (EC2 t3.medium in us-west-2)",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Deploy EC2 instance t3.medium 50GB gp3 Ubuntu in us-west-2"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_vm",
        "expected_payload_keys": ["instance_type", "region", "cloud_provider", "os", "volume_size"],
    },
    {
        "id": 2,
        "name": "Provision Kubernetes (EKS 3-node cluster)",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create an EKS cluster, 3 nodes, m5.large, kubernetes 1.29 in us-east-1"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_kubernetes",
        "expected_payload_keys": ["cluster_name", "node_count", "node_type", "kubernetes_version", "region"],
    },
    {
        "id": 3,
        "name": "Provision Docker (Nginx container)",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Run a nginx Docker container, port 80:80"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_docker",
        "expected_payload_keys": ["docker_image", "container_name", "ports"],
    },
    {
        "id": 4,
        "name": "Provision Database (PostgreSQL 16)",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Deploy PostgreSQL database, version 16, name analytics_db, user admin"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_database",
        "expected_payload_keys": ["database_engine", "database_name", "database_user", "port"],
    },
    {
        "id": 5,
        "name": "Provision FastAPI application",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Deploy FastAPI app billing-api, port 8000, http port 80"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_fastapi",
        "expected_payload_keys": ["app_name", "app_port", "http_port"],
    },
    {
        "id": 6,
        "name": "Provision Static Website",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Deploy static website to nginx on docs.example.com, port 80"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_static_website",
        "expected_payload_keys": ["server_name", "http_port"],
    },
    {
        "id": 7,
        "name": "Provision RDS MySQL",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Deploy an RDS MySQL 8.0 instance, db.r5.large, 100GB storage, multi-AZ in us-east-1"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_database",
        "expected_payload_keys": ["database_engine", "region"],
    },
    {
        "id": 8,
        "name": "Provision GKE cluster",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Deploy a GKE cluster in us-central1, 5 nodes, n2-standard-4, kubernetes 1.28"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_kubernetes",
        "expected_payload_keys": ["node_count", "node_type"],
    },
    {
        "id": 9,
        "name": "Provision Redis container",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Run a Redis Docker container on port 6379:6379 with persistent volume"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_docker",
        "expected_payload_keys": ["docker_image", "ports"],
    },
    {
        "id": 10,
        "name": "Provision IAM Role (EC2+S3)",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create an IAM role for EC2 instances with S3 read access"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_iam",
        "expected_payload_keys": [],
    },
    {
        "id": 11,
        "name": "Provision VPC with NAT",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create a VPC with CIDR 10.0.0.0/16 and NAT gateway in us-east-1"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_network",
        "expected_payload_keys": [],
    },
    {
        "id": 12,
        "name": "Provision Security Group",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create a security group allowing SSH, HTTP, and HTTPS from anywhere"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_network",
        "expected_payload_keys": [],
    },
    {
        "id": 13,
        "name": "Provision Application Load Balancer",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create an Application Load Balancer with target group on port 80"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_network",
        "expected_payload_keys": [],
    },
    {
        "id": 14,
        "name": "Provision IAM Policy (S3 custom)",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create an IAM policy for custom S3 bucket access to my-data-bucket"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_iam",
        "expected_payload_keys": [],
    },
    {
        "id": 15,
        "name": "Provision VPC Peering",
        "endpoint": "/api/cloud/provision-intent",
        "payload": {"query": "Create a VPC peering connection between prod and staging VPCs"},
        "expected_query_type": "provisioning",
        "expected_intent": "provision_network",
        "expected_payload_keys": [],
    },
]


# ============================================================================
# HTTP HELPERS
# ============================================================================

def _post(path: str, json_body: dict, timeout: float = 60.0) -> dict:
    url = f"{BASE_URL}{path}"
    start = time.time()
    if httpx:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=json_body)
    else:
        resp = _requests_lib.post(url, json=json_body, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text[:500]}
    print(f"\n  POST {path}  [{resp.status_code}]  {elapsed_ms:.0f}ms")
    return {"status_code": resp.status_code, "body": body, "elapsed_ms": elapsed_ms}


def _get(path: str, params: dict = None, timeout: float = 30.0) -> dict:
    url = f"{BASE_URL}{path}"
    start = time.time()
    if httpx:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
    else:
        resp = _requests_lib.get(url, params=params, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text[:500]}
    print(f"\n  GET  {path}  [{resp.status_code}]  {elapsed_ms:.0f}ms")
    return {"status_code": resp.status_code, "body": body, "elapsed_ms": elapsed_ms}


def _score_response(result: dict, test_name: str, *, expect_success: bool = True) -> int:
    score = 1
    body = result["body"]
    status = result["status_code"]
    details = []

    if expect_success:
        if status == 200:
            score = 5
        elif status in (201, 202):
            score = 5
        elif status == 503:
            score = 3
            details.append("service unavailable (not initialized)")
        elif status == 500:
            score = 2
            details.append(f"server error: {str(body.get('detail', ''))[:80]}")
        else:
            score = 2
            details.append(f"unexpected status {status}")

        if isinstance(body, dict):
            if body.get("status") == "healthy" or body.get("response"):
                score += 2
            if result["elapsed_ms"] < 5000:
                score += 1
            if result["elapsed_ms"] < 2000:
                score += 1
            if len(body) > 3:
                score += 1
    else:
        if status in (400, 422):
            score = 8
        elif status == 200 and (body.get("query_type") == "other" or body.get("intent") is None):
            score = 7
        else:
            score = 3
            details.append(f"expected error but got {status}")

    _record_score(test_name, min(score, 10), "; ".join(details) if details else f"HTTP {status}")
    return score


# ============================================================================
# SECTION 1: API TESTS (requires running server)
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestAPIHealth:
    """Core health and status endpoints."""

    def test_api_health_check(self):
        """GET /health - basic health check."""
        r = _get("/health")
        _score_response(r, "GET /health")
        if r["status_code"] == 200:
            assert r["body"].get("status") == "healthy"

    def test_api_stats(self):
        """GET /stats - vector store statistics."""
        r = _get("/stats")
        score = _score_response(r, "GET /stats")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  Vector count: {body.get('total_vectors', body.get('vector_count', 'N/A'))}")

    def test_api_logs(self):
        """GET /logs - recent log entries."""
        r = _get("/logs", params={"lines": 10})
        _score_response(r, "GET /logs")
        if r["status_code"] == 200:
            print(f"  Total log lines: {r['body'].get('total_lines', 'N/A')}")
            print(f"  Showing: {r['body'].get('showing', 'N/A')}")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestAPIVectorSearch:
    """Vector similarity search endpoints."""

    def test_api_search(self):
        """POST /search - vector similarity search."""
        r = _post("/search", {"query": "deploy EC2 instance with Ubuntu", "top_k": 5})
        _score_response(r, "POST /search")
        if r["status_code"] == 200:
            results = r["body"].get("results", [])
            print(f"  Results: {len(results)}")
            for i, res in enumerate(results[:3]):
                text = str(res.get("text", ""))[:80]
                score = res.get("score", 0)
                print(f"    #{i+1}: score={score:.4f} | {text}...")

    def test_api_generate(self):
        """POST /generate - LLM text generation."""
        r = _post("/generate", {"prompt": "How to deploy a Docker container", "max_new_tokens": 100})
        _score_response(r, "POST /generate")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  Model loaded: {body.get('model_loaded')}")
            print(f"  Device: {body.get('device')}")
            response_text = body.get("response", "")[:150]
            print(f"  Response: {response_text}...")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestAPIV1RAG:
    """V1 RAG + Reasoning endpoints."""

    def test_api_v1_query_with_reasoning(self):
        """POST /api/models/v1/query - RAG query with chain-of-thought reasoning."""
        r = _post("/api/models/v1/query", {
            "query": "Deploy a small EC2 instance with 30GB disk in us-east-1 with Ubuntu",
            "include_reasoning": True,
            "top_k": 5,
        })
        _score_response(r, "V1 RAG query (with reasoning)")
        if r["status_code"] == 200:
            body = r["body"]
            reasoning = body.get("reasoning", {})
            context = body.get("context", [])
            print(f"  Intent: {reasoning.get('intent')}")
            print(f"  Confidence: {reasoning.get('confidence', 0):.2f}")
            print(f"  Steps: {len(reasoning.get('steps', []))}")
            print(f"  Context docs: {len(context)}")
            response_text = (body.get("response") or "")[:200]
            if response_text:
                print(f"  Response: {response_text}...")

    def test_api_v1_query_without_reasoning(self):
        """POST /api/models/v1/query - simple search without reasoning."""
        r = _post("/api/models/v1/query", {
            "query": "What is Kubernetes?",
            "include_reasoning": False,
            "top_k": 3,
        })
        _score_response(r, "V1 simple query (no reasoning)")
        if r["status_code"] == 200:
            context = r["body"].get("context", [])
            print(f"  Context docs: {len(context)}")

    def test_api_v1_developer(self):
        """POST /api/models/v1/developer - developer assistance with code."""
        r = _post("/api/models/v1/developer", {
            "query": "Create a VPC with private subnets and flow logs in Terraform",
            "include_code": True,
            "include_reasoning": True,
        })
        _score_response(r, "V1 developer endpoint")
        if r["status_code"] == 200:
            body = r["body"]
            code_examples = body.get("code_examples", [])
            print(f"  Code examples: {len(code_examples)}")
            if code_examples:
                print(f"  First example type: {code_examples[0].get('type')}")

    def test_api_v1_terminal(self):
        """POST /api/models/v1/terminal - terminal/CLI assistance."""
        r = _post("/api/models/v1/terminal", {
            "command": "kubectl get pods not responding",
            "include_explanation": True,
        })
        _score_response(r, "V1 terminal endpoint")
        if r["status_code"] == 200:
            body = r["body"]
            incidents = body.get("incidents", [])
            recommendations = body.get("recommendations", [])
            print(f"  Incidents: {len(incidents)}")
            print(f"  Recommendations: {len(recommendations)}")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestAPIV2NLP:
    """V2 NLP + Entity Extraction endpoints."""

    def test_api_v2_query(self):
        """POST /api/models/v2/query - NLP-enhanced query."""
        r = _post("/api/models/v2/query", {
            "query": "EC2 instance i-0abc123 in us-east-1 showing high CPU and OOM errors",
            "extract_entities": True,
            "include_recommendations": True,
            "top_k": 5,
        })
        _score_response(r, "V2 NLP query")
        if r["status_code"] == 200:
            body = r["body"]
            entities = body.get("entities", [])
            recommendations = body.get("recommendations", [])
            entity_summary = body.get("entity_summary", {})
            print(f"  Entities found: {entity_summary.get('total', len(entities))}")
            print(f"  Categories: {list(entity_summary.get('by_category', {}).keys())}")
            print(f"  Recommendations: {len(recommendations)}")
            for rec in recommendations[:3]:
                print(f"    - {rec[:80]}")

    def test_api_v2_extract(self):
        """POST /api/models/v2/extract - entity extraction."""
        r = _post("/api/models/v2/extract", {
            "text": "Deploy FastAPI on EKS cluster us-west-2, use Terraform with Prometheus monitoring on port :8080",
        })
        _score_response(r, "V2 entity extraction")
        if r["status_code"] == 200:
            body = r["body"]
            summary = body.get("summary", {})
            print(f"  Total entities: {summary.get('total_entities', 0)}")
            print(f"  Categories: {summary.get('categories', [])}")
            print(f"  Cloud services: {summary.get('cloud_services', [])}")

    def test_api_v2_status(self):
        """GET /api/models/v2/status - NLP capabilities."""
        r = _get("/api/models/v2/status")
        _score_response(r, "V2 NLP status")
        if r["status_code"] == 200:
            body = r["body"]
            caps = body.get("capabilities", {})
            for cap_name, cap_info in caps.items():
                available = cap_info.get("available", False)
                status = "available" if available else "not available"
                print(f"  {cap_name}: {status}")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestAPIV3Incidents:
    """V3 Incident pattern analysis."""

    def test_api_v3_incident_analysis(self):
        """POST /api/models/v3/query - unusual incident patterns."""
        r = _post("/api/models/v3/query", {
            "query": "EKS cluster node failures and pod evictions in us-east-1",
            "top_k": 10,
            "include_reasoning": True,
            "focus": "cloud_devops",
        })
        _score_response(r, "V3 incident analysis")
        if r["status_code"] == 200:
            body = r["body"]
            metrics = body.get("metrics", {})
            unusual = body.get("unusual_incidents", [])
            performance = body.get("performance", {})
            print(f"  Total incidents: {metrics.get('total_incidents', 0)}")
            print(f"  Unusual count: {metrics.get('unusual_count', 0)}")
            print(f"  Unusual rate: {metrics.get('unusual_rate', 0):.3f}")
            print(f"  Signals used: {body.get('signals_used', [])}")
            if performance:
                print(f"  Performance: search={performance.get('local_search_ms', 0):.1f}ms "
                      f"analysis={performance.get('analysis_ms', 0):.1f}ms "
                      f"total={performance.get('total_ms', 0):.1f}ms")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestAPICloudProvisioning:
    """Cloud provisioning intent endpoints."""

    def test_provision_vm(self):
        """Provision VM (EC2 t3.medium in us-west-2)."""
        t = PROVISION_TESTS[0]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_kubernetes(self):
        """Provision Kubernetes (EKS 3-node cluster)."""
        t = PROVISION_TESTS[1]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_docker(self):
        """Provision Docker (Nginx container)."""
        t = PROVISION_TESTS[2]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_database(self):
        """Provision Database (PostgreSQL 16)."""
        t = PROVISION_TESTS[3]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_fastapi(self):
        """Provision FastAPI application."""
        t = PROVISION_TESTS[4]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_static_website(self):
        """Provision Static Website."""
        t = PROVISION_TESTS[5]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_rds_mysql(self):
        """Provision RDS MySQL instance."""
        t = PROVISION_TESTS[6]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_gke(self):
        """Provision GKE cluster."""
        t = PROVISION_TESTS[7]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_redis_docker(self):
        """Provision Redis Docker container."""
        t = PROVISION_TESTS[8]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_iam_role(self):
        """Provision IAM Role (EC2+S3)."""
        t = PROVISION_TESTS[9]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_vpc(self):
        """Provision VPC with NAT gateway."""
        t = PROVISION_TESTS[10]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_security_group(self):
        """Provision Security Group."""
        t = PROVISION_TESTS[11]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_load_balancer(self):
        """Provision Application Load Balancer."""
        t = PROVISION_TESTS[12]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_iam_policy(self):
        """Provision IAM Policy (S3 custom)."""
        t = PROVISION_TESTS[13]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_vpc_peering(self):
        """Provision VPC Peering."""
        t = PROVISION_TESTS[14]
        r = _post(t["endpoint"], t["payload"])
        _score_response(r, t["name"])
        if r["status_code"] == 200:
            self._print_provision_result(r["body"], t)

    def test_provision_non_provisioning_query(self):
        """Non-provisioning query should return query_type='other'."""
        r = _post("/api/cloud/provision-intent", {
            "query": "What is the weather today?",
        })
        _score_response(r, "Non-provisioning query (expect 'other')", expect_success=False)
        if r["status_code"] == 200:
            assert r["body"].get("intent") is None or r["body"].get("query_type") == "other"

    def test_provision_empty_query(self):
        """Empty query should return query_type='other'."""
        r = _post("/api/cloud/provision-intent", {"query": ""})
        _score_response(r, "Empty provisioning query", expect_success=False)
        if r["status_code"] == 200:
            assert r["body"].get("query_type") == "other"

    @staticmethod
    def _print_provision_result(body: dict, test: dict):
        qt = body.get("query_type", "unknown")
        intent = body.get("intent")
        confidence = body.get("confidence", 0)
        payload = body.get("payload") or {}
        print(f"  query_type={qt}, intent={intent}, confidence={confidence:.4f}")
        errors = []
        expected_qt = test.get("expected_query_type")
        if expected_qt and qt != expected_qt:
            errors.append(f"query_type: expected '{expected_qt}', got '{qt}'")
        expected_intent = test.get("expected_intent")
        if expected_intent and intent != expected_intent:
            errors.append(f"intent: expected '{expected_intent}', got '{intent}'")
        for key in test.get("expected_payload_keys", []):
            if key not in payload:
                errors.append(f"payload missing: '{key}'")
        if errors:
            for err in errors:
                print(f"  WARNING: {err}")
        if payload:
            for k in sorted(payload.keys()):
                v = payload[k]
                if v and str(v).strip().lower() not in ("", "nan", "none"):
                    print(f"    {k}: {v}")


# ============================================================================
# SECTION 2: UNIT TESTS (no server required)
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestUnitEntityExtraction:
    """Direct entity extraction tests (no server needed)."""

    def test_unit_entity_extraction_vm(self):
        """Extract VM provisioning entities from query."""
        try:
            from app.services.ai.ml.entity_extraction import EntityExtractor
        except ImportError:
            from services.ai.ml.entity_extraction import EntityExtractor

        extractor = EntityExtractor()
        query = "Deploy EC2 instance t3.medium 50GB gp3 Ubuntu in us-west-2"
        extracted = extractor.extract_entities(query)

        score = 3
        details = []

        if extracted.get("instance_type") == "t3.medium":
            score += 2
            print(f"  instance_type: {extracted['instance_type']}")
        else:
            details.append(f"instance_type: got '{extracted.get('instance_type')}'")

        if extracted.get("region") == "us-west-2":
            score += 2
            print(f"  region: {extracted['region']}")
        else:
            details.append(f"region: got '{extracted.get('region')}'")

        volume = extracted.get("volume_size_gb") or extracted.get("volume_size")
        if volume and "50" in str(volume):
            score += 2
            print(f"  volume: {volume}")
        else:
            details.append(f"volume: got '{volume}'")

        extra = {k: v for k, v in extracted.items()
                 if k not in ("instance_type", "region", "volume_size_gb", "volume_size")
                 and v and str(v).strip().lower() not in ("", "nan", "none")}
        if extra:
            print(f"  Extra: {extra}")
            score = min(score + 1, 10)

        _record_score("Unit: Entity Extraction (VM)", min(score, 10),
                       "; ".join(details) if details else "All entities extracted")

    def test_unit_entity_extraction_kubernetes(self):
        """Extract Kubernetes provisioning entities."""
        try:
            from app.services.ai.ml.entity_extraction import EntityExtractor
        except ImportError:
            from services.ai.ml.entity_extraction import EntityExtractor

        extractor = EntityExtractor()
        query = "Create an EKS cluster, 3 nodes, m5.large, kubernetes 1.29 in us-east-1"
        extracted = extractor.extract_entities(query)

        score = 3
        details = []

        checks = [
            ("instance_type", "m5.large"),
            ("region", "us-east-1"),
            ("kubernetes_version", "1.29"),
            ("node_count", "3"),
        ]
        for key, expected in checks:
            actual = str(extracted.get(key, ""))
            if expected in actual:
                score += 1
                print(f"  {key}: {actual}")
            else:
                details.append(f"{key}: expected '{expected}', got '{actual}'")

        _record_score("Unit: Entity Extraction (K8s)", min(score + 2, 10),
                       "; ".join(details) if details else "All entities extracted")

    def test_unit_entity_extraction_docker(self):
        """Extract Docker provisioning entities."""
        try:
            from app.services.ai.ml.entity_extraction import EntityExtractor
        except ImportError:
            from services.ai.ml.entity_extraction import EntityExtractor

        extractor = EntityExtractor()
        query = "Run a nginx Docker container, port 80:80"
        extracted = extractor.extract_entities(query)

        score = 3
        details = []

        if extracted.get("docker_image") == "nginx" or extracted.get("image") == "nginx":
            score += 3
            print(f"  docker_image: nginx")
        else:
            details.append(f"docker_image: got '{extracted.get('docker_image')}'")

        if extracted.get("ports") == "80:80":
            score += 2
            print(f"  ports: 80:80")
        else:
            details.append(f"ports: got '{extracted.get('ports')}'")

        _record_score("Unit: Entity Extraction (Docker)", min(score + 2, 10),
                       "; ".join(details) if details else "All entities extracted")

    def test_unit_entity_extraction_database(self):
        """Extract database provisioning entities."""
        try:
            from app.services.ai.ml.entity_extraction import EntityExtractor
        except ImportError:
            from services.ai.ml.entity_extraction import EntityExtractor

        extractor = EntityExtractor()
        query = "Deploy PostgreSQL database, version 16, name analytics_db, user admin"
        extracted = extractor.extract_entities(query)

        score = 3
        details = []

        if extracted.get("database_name") == "analytics_db":
            score += 2
            print(f"  database_name: analytics_db")
        else:
            details.append(f"database_name: got '{extracted.get('database_name')}'")

        if extracted.get("database_user") == "admin":
            score += 2
            print(f"  database_user: admin")
        else:
            details.append(f"database_user: got '{extracted.get('database_user')}'")

        ver = extracted.get("postgres_version") or extracted.get("kubernetes_version")
        if ver and "16" in str(ver):
            score += 2
            print(f"  version: {ver}")
        else:
            details.append(f"version: got '{ver}'")

        _record_score("Unit: Entity Extraction (Database)", min(score + 1, 10),
                       "; ".join(details) if details else "All entities extracted")

    def test_unit_entity_extraction_static_website(self):
        """Extract static website provisioning entities."""
        try:
            from app.services.ai.ml.entity_extraction import EntityExtractor
        except ImportError:
            from services.ai.ml.entity_extraction import EntityExtractor

        extractor = EntityExtractor()
        query = "Deploy static website to nginx on docs.example.com, port 80"
        extracted = extractor.extract_entities(query)

        score = 3
        details = []

        hostname = extracted.get("hostname") or extracted.get("server_name")
        if hostname and "docs.example.com" in hostname:
            score += 3
            print(f"  hostname: {hostname}")
        else:
            details.append(f"hostname: got '{hostname}'")

        http_port = extracted.get("http_port")
        if http_port and int(http_port) == 80:
            score += 2
            print(f"  http_port: {http_port}")
        else:
            details.append(f"http_port: got '{http_port}'")

        _record_score("Unit: Entity Extraction (Website)", min(score + 2, 10),
                       "; ".join(details) if details else "All entities extracted")


# ============================================================================
# INTERACTIVE CHAT MODE
# ============================================================================

_PROVISION_KEYWORDS = [
    "deploy", "provision", "create", "launch", "set up", "setup", "spin up",
    "host", "start", "run", "install",
    "ec2", "instance", "vm", "virtual machine", "server",
    "kubernetes", "eks", "aks", "gke", "k8s", "cluster", "node",
    "docker", "container", "nginx", "image",
    "database", "postgres", "mysql", "rds", "mongodb", "db",
    "fastapi", "flask", "django", "api", "app",
    "website", "static site", "static website", "s3 bucket",
    "iam", "role", "policy", "user", "service account", "keypair", "key pair",
    "secret", "cloudtrail",
    "vpc", "subnet", "security group", "load balancer", "alb", "nlb",
    "elastic ip", "route table", "nat gateway", "vpn", "peering",
    "transit gateway", "dns record", "acl", "firewall", "nsg", "vnet",
]


def _is_provision_query(query: str) -> bool:
    q = query.lower()
    return sum(1 for kw in _PROVISION_KEYWORDS if kw in q) >= 2


def _print_provision_response(data: dict) -> None:
    qt = data.get("query_type", "unknown")
    intent = data.get("intent")
    confidence = data.get("confidence", 0)
    payload = data.get("payload") or {}

    print(f"\n  Query Type:  {qt}")
    if intent:
        print(f"  Intent:      {intent}")
    print(f"  Confidence:  {confidence:.4f}")

    if payload:
        print(f"\n  Payload (Golang-ready):")
        for k, v in payload.items():
            if v and str(v).lower() not in ("", "nan"):
                print(f"    {k}: {v}")


def _print_rag_response(data: dict) -> None:
    response_text = data.get("response", "")
    reasoning = data.get("reasoning") or {}
    context = data.get("context") or []

    if response_text:
        print(f"\n  Response:")
        for line in response_text[:800].split("\n"):
            print(f"    {line}")
        if len(response_text) > 800:
            print(f"    ... ({len(response_text)} chars total)")

    if reasoning:
        print(f"\n  Reasoning:")
        print(f"    Intent:     {reasoning.get('intent', 'unknown')}")
        print(f"    Confidence: {reasoning.get('confidence', 0):.2%}")

    if context:
        print(f"\n  Context: {len(context)} documents")


def _process_chat_query(session, user_input: str) -> None:
    if user_input.startswith("/cloud "):
        query = user_input[7:].strip()
        endpoint = "/api/cloud/provision-intent"
        payload = {"query": query}
        mode = "provision-intent"
    elif user_input.startswith("/rag "):
        query = user_input[5:].strip()
        endpoint = "/api/models/v1/query"
        payload = {"query": query, "include_reasoning": True, "top_k": 5}
        mode = "rag"
    elif user_input.startswith("/dev "):
        query = user_input[5:].strip()
        endpoint = "/api/models/v1/developer"
        payload = {"query": query, "include_code": True, "include_reasoning": True}
        mode = "developer"
    elif user_input.startswith("/v2 "):
        query = user_input[4:].strip()
        endpoint = "/api/models/v2/query"
        payload = {"query": query, "extract_entities": True, "include_recommendations": True}
        mode = "v2-nlp"
    elif user_input.startswith("/v3 "):
        query = user_input[4:].strip()
        endpoint = "/api/models/v3/query"
        payload = {"query": query, "include_reasoning": True, "focus": "cloud_devops"}
        mode = "v3-incidents"
    elif _is_provision_query(user_input):
        endpoint = "/api/cloud/provision-intent"
        payload = {"query": user_input}
        mode = "provision-intent"
    else:
        endpoint = "/api/models/v1/query"
        payload = {"query": user_input, "include_reasoning": True, "top_k": 5}
        mode = "rag"

    print(f"\n  [{mode}] -> {endpoint}")

    start = time.perf_counter()
    try:
        r = session.post(f"{BASE_URL}{endpoint}", json=payload, timeout=60)
        data = r.json()
    except Exception as e:
        print(f"\n  Error: {e}")
        return
    duration_ms = (time.perf_counter() - start) * 1000

    if r.status_code != 200:
        print(f"\n  Error [{r.status_code}]: {data.get('detail', data)}")
        return

    print(f"  Responded in {duration_ms:.0f}ms")

    if mode == "provision-intent":
        _print_provision_response(data)
    else:
        _print_rag_response(data)


def run_batch_tests(base_url: str = BASE_URL) -> None:
    """Run all provisioning tests in batch mode."""
    print("\n" + "=" * 78)
    print("  VaLLM Regression Tests - Batch Mode")
    print("=" * 78)
    print(f"  Base URL: {base_url}")
    print(f"  Tests:    {len(PROVISION_TESTS)} provisioning + API + unit")
    print("=" * 78)

    session = _requests_lib.Session()
    session.headers.update({"Content-Type": "application/json"})

    print("\nChecking service health...", end=" ")
    try:
        r = session.get(f"{base_url}/health", timeout=5)
        if r.status_code != 200:
            print("FAILED")
            print(f"\nService not available at {base_url}. Start the app first:")
            print("  uvicorn app.app:app --host 0.0.0.0 --port 8746")
            return
        print("OK\n")
    except Exception:
        print("FAILED")
        print(f"\nCannot connect to {base_url}. Start the app first.")
        return

    passed = 0
    failed = 0

    for test in PROVISION_TESTS:
        test_id = test["id"]
        test_name = test["name"]
        endpoint = test["endpoint"]
        payload = test["payload"]

        print(f"[{test_id:02d}/{len(PROVISION_TESTS)}] {test_name}")
        print(f"        Endpoint: {endpoint}")
        print(f"        Query:    {payload.get('query', '')[:70]}...")

        start = time.perf_counter()
        try:
            r = session.post(f"{base_url}{endpoint}", json=payload, timeout=60)
            data = r.json()
        except Exception as e:
            data = {"_error": str(e)}
        duration_ms = (time.perf_counter() - start) * 1000

        errors = []
        if "_error" in data:
            errors.append(f"Request failed: {data['_error']}")
        else:
            actual_qt = data.get("query_type")
            expected_qt = test.get("expected_query_type")
            if expected_qt and actual_qt != expected_qt:
                errors.append(f"query_type: expected '{expected_qt}', got '{actual_qt}'")
            actual_intent = data.get("intent")
            expected_intent = test.get("expected_intent")
            if expected_intent and actual_intent != expected_intent:
                errors.append(f"intent: expected '{expected_intent}', got '{actual_intent}'")
            for key in test.get("expected_payload_keys", []):
                if key not in (data.get("payload") or {}):
                    errors.append(f"payload missing: '{key}'")
            confidence = data.get("confidence", 0)
            if expected_qt == "provisioning" and confidence < 0.2:
                errors.append(f"confidence too low: {confidence:.4f}")

        if errors:
            failed += 1
            print(f"        Status:   FAIL ({duration_ms:.0f}ms)")
            for err in errors:
                print(f"          - {err}")
        else:
            passed += 1
            print(f"        Status:   PASS ({duration_ms:.0f}ms)")
            print(f"          query_type={data.get('query_type')}, "
                  f"intent={data.get('intent')}, "
                  f"confidence={data.get('confidence', 0):.4f}")
        print()

    print("=" * 78)
    print(f"  RESULTS: {passed} passed, {failed} failed, {len(PROVISION_TESTS)} total")
    print(f"  Pass Rate: {passed / len(PROVISION_TESTS) * 100:.0f}%")
    print("=" * 78)


def interactive_mode(base_url: str = BASE_URL, initial_query: str = "") -> None:
    """Interactive chat mode."""
    print("\n" + "=" * 78)
    print("  VaLLM Interactive Chat")
    print("=" * 78)
    print("  Ask anything about cloud infrastructure. Auto-routes your query.")
    print()
    print("  Prefixes:")
    print("    /cloud   Force provision-intent endpoint")
    print("    /rag     Force RAG query endpoint")
    print("    /dev     Force developer endpoint (includes Terraform)")
    print("    /v2      Force V2 NLP query (entity extraction)")
    print("    /v3      Force V3 incident analysis")
    print()
    print("  Commands:")
    print("    /health  Check service health")
    print("    /tests   Run batch provisioning tests")
    print("    /quit    Exit")
    print("=" * 78)

    session = _requests_lib.Session()
    session.headers.update({"Content-Type": "application/json"})

    print(f"\n  Connecting to {base_url}...", end=" ")
    try:
        r = session.get(f"{base_url}/health", timeout=5)
        if r.status_code != 200:
            print("FAILED")
            return
        print("OK")
    except Exception:
        print("FAILED - start the app first")
        return

    turn = 0

    if initial_query:
        turn += 1
        print(f"\n{'=' * 78}")
        print(f"  [{turn}] You: {initial_query}")
        _process_chat_query(session, initial_query)

    while True:
        try:
            print()
            prompt = "  What would you like to do? > " if turn == 0 else "  Next question > "
            user_input = input(prompt).strip()
            if not user_input:
                continue
            lower = user_input.lower()
            if lower in ("/quit", "/exit", "quit", "exit", "q"):
                print(f"\n  Session ended. {turn} question(s) answered. Goodbye!")
                break
            if lower == "/health":
                try:
                    r = session.get(f"{base_url}/health", timeout=5)
                    print(f"  Health: {'OK' if r.status_code == 200 else 'Unhealthy'}")
                except Exception:
                    print("  Health: Unreachable")
                continue
            if lower == "/tests":
                print()
                run_batch_tests(base_url)
                continue

            turn += 1
            print(f"\n{'=' * 78}")
            print(f"  [{turn}] You: {user_input}")
            _process_chat_query(session, user_input)

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  Session ended. {turn} question(s) answered. Goodbye!")
            break
        except Exception as e:
            print(f"  Error: {e}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="VaLLM Regression Test Suite & Interactive Chat",
        epilog=(
            "Examples:\n"
            "  python -m app.tests.tests                                    # batch tests\n"
            "  python -m app.tests.tests --interactive                      # chat mode\n"
            '  python -m app.tests.tests --interactive "deploy ec2 20gb"    # chat with query\n'
            "  python -m app.tests.tests --url http://localhost:8746        # custom URL\n"
            "\n"
            "  pytest app/tests/tests.py -v -s                             # pytest all\n"
            "  pytest app/tests/tests.py -v -s -k 'api'                    # pytest API only\n"
            "  pytest app/tests/tests.py -v -s -k 'unit'                   # pytest unit only\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--interactive", nargs="?", const="", default=None,
                        metavar="QUERY",
                        help="Start interactive chat (optionally with an initial query)")
    parser.add_argument("--url", default=BASE_URL,
                        help=f"Base URL (default: {BASE_URL})")
    args = parser.parse_args()

    if args.interactive is not None:
        interactive_mode(args.url, args.interactive)
    else:
        run_batch_tests(args.url)
