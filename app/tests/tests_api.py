"""
VaLLM API Regression Tests - Comprehensive Endpoint Coverage
=============================================================

Author: Joel Otepa Wembo
https://joelwembo.com

DESCRIPTION
===========
Self-contained pytest test suite that exercises every endpoint exposed by
VaLLM via real HTTP requests.  Tests cover:

    ── Core ──────────────────────────────────────────────────────────
    GET  /health                          Health check
    GET  /stats                           Vector store stats
    GET  /logs                            Recent logs
    GET  /logs/stats                      Log statistics
    POST /search                          Vector similarity search
    POST /generate                        LLM text generation

    ── V1 (RAG + Reasoning) ──────────────────────────────────────────
    POST /api/models/v1/query             RAG query with reasoning
    POST /api/models/v1/developer         Developer assistance
    POST /api/models/v1/terminal          Terminal/CLI assistance

    ── V2 (NLP + Entity Extraction) ──────────────────────────────────
    POST /api/models/v2/query             NLP-enhanced query
    POST /api/models/v2/extract           Entity extraction
    GET  /api/models/v2/status            NLP capabilities

    ── V3 (Incident Patterns) ────────────────────────────────────────
    POST /api/models/v3/query             Unusual incident patterns

    ── Cloud Provisioning (Intent Detection) ─────────────────────────
    POST /api/cloud/provision-intent      6 provisioning types
         Detects deployment/provisioning intents and extracts
         parameters.  Not for monitoring or status checks.

PREREQUISITES
=============
    pip install pytest httpx requests

USAGE
=====
    # Start the app first:
    uvicorn app.app:app --host 0.0.0.0 --port 8746

    # Run all API tests
    pytest app/tests/tests_api.py -v -s

    # Run only provisioning tests
    pytest app/tests/tests_api.py -v -s -k "Provision"

    # Run only V1 tests
    pytest app/tests/tests_api.py -v -s -k "V1"
"""

import atexit
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import httpx
except ImportError:
    httpx = None

import requests

BASE_URL = os.environ.get("VALLM_TEST_URL", "http://localhost:8746")
_WRAP_WIDTH = 90

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
    print("  VALLM API REGRESSION - FINAL SCORECARD")
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


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 200) -> str:
    """Truncate long strings for display."""
    text = str(text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _print_request(method: str, path: str, payload: Optional[dict] = None,
                   params: Optional[dict] = None):
    """Print the request that was sent."""
    print(f"\n  ┌─ REQUEST ─────────────────────────────────────────────────")
    print(f"  │ {method} {BASE_URL}{path}")
    if params:
        print(f"  │ Params: {json.dumps(params)}")
    if payload:
        for key, val in payload.items():
            display = _truncate(str(val), 120)
            print(f"  │   {key}: {display}")
    print(f"  └──────────────────────────────────────────────────────────")


def _print_response(status: int, elapsed_ms: float, body: dict,
                    highlight_keys: Optional[List[str]] = None):
    """Print the response received."""
    print(f"  ┌─ RESPONSE [{status}] ({elapsed_ms:.0f}ms) ────────────────────────────")
    if not highlight_keys:
        highlight_keys = ["response", "answer", "text", "generated_text",
                          "status", "intent", "query_type", "confidence",
                          "reasoning", "result", "message", "detail"]
    for key in highlight_keys:
        if key in body:
            val = body[key]
            if isinstance(val, dict):
                print(f"  │ {key}:")
                for k2, v2 in val.items():
                    print(f"  │   {k2}: {_truncate(str(v2), 100)}")
            elif isinstance(val, list):
                print(f"  │ {key}: [{len(val)} items]")
                for i, item in enumerate(val[:3]):
                    print(f"  │   [{i}] {_truncate(str(item), 100)}")
                if len(val) > 3:
                    print(f"  │   ... and {len(val) - 3} more")
            else:
                print(f"  │ {key}: {_truncate(str(val), 150)}")
    shown = set(highlight_keys)
    remaining = {k: v for k, v in body.items() if k not in shown and k != "_raw"}
    if remaining:
        others = list(remaining.keys())[:8]
        print(f"  │ other fields: {', '.join(others)}")
    print(f"  └──────────────────────────────────────────────────────────")


def _post(path: str, json_body: dict, timeout: float = 60.0) -> dict:
    url = f"{BASE_URL}{path}"
    _print_request("POST", path, payload=json_body)
    start = time.time()
    if httpx:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=json_body)
    else:
        resp = requests.post(url, json=json_body, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text[:500]}
    _print_response(resp.status_code, elapsed_ms, body)
    return {"status_code": resp.status_code, "body": body, "elapsed_ms": elapsed_ms}


def _get(path: str, params: dict = None, timeout: float = 30.0) -> dict:
    url = f"{BASE_URL}{path}"
    _print_request("GET", path, params=params)
    start = time.time()
    if httpx:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
    else:
        resp = requests.get(url, params=params, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text[:500]}
    _print_response(resp.status_code, elapsed_ms, body)
    return {"status_code": resp.status_code, "body": body, "elapsed_ms": elapsed_ms}


def _score_http(result: dict, test_name: str, *, expect_success: bool = True) -> int:
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
            details.append("service unavailable")
        elif status == 500:
            score = 2
            details.append(f"server error: {str(body.get('detail', ''))[:80]}")
        else:
            score = 2
            details.append(f"unexpected status {status}")

        if isinstance(body, dict) and len(body) > 2:
            score += 1
        if result["elapsed_ms"] < 5000:
            score += 1
        if result["elapsed_ms"] < 2000:
            score += 1
        if isinstance(body, dict) and (body.get("status") == "healthy" or body.get("response")):
            score += 2
    else:
        if status in (400, 422):
            score = 8
        elif status == 200 and body.get("query_type") == "other":
            score = 7
        else:
            score = 3
            details.append(f"expected error but got {status}")

    _record_score(test_name, min(score, 10), "; ".join(details) if details else f"HTTP {status}")
    return score


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestCoreEndpoints:
    """Core health, stats, logs, search, generate."""

    def test_health(self):
        r = _get("/health")
        _score_http(r, "GET /health")
        assert r["status_code"] == 200
        assert r["body"].get("status") == "healthy"

    def test_stats(self):
        r = _get("/stats")
        _score_http(r, "GET /stats")

    def test_logs(self):
        r = _get("/logs", params={"lines": 10})
        _score_http(r, "GET /logs")

    def test_logs_stats(self):
        r = _get("/logs/stats")
        _score_http(r, "GET /logs/stats")

    def test_search_cloud_query(self):
        query = "deploy kubernetes cluster"
        r = _post("/search", {"query": query, "top_k": 5})
        _score_http(r, "POST /search (K8s)")
        if r["status_code"] == 200:
            results = r["body"].get("results", [])
            print(f"  ── Search Results for: \"{query}\" ──")
            print(f"  Matches: {len(results)}")
            for i, res in enumerate(results[:3]):
                print(f"    #{i+1}: score={res.get('score', 0):.4f} | "
                      f"{_truncate(str(res.get('text', '')), 100)}")
                if res.get("intent"):
                    print(f"          intent: {res['intent']}")

    def test_search_devops_query(self):
        query = "terraform VPC subnet security group"
        r = _post("/search", {"query": query, "top_k": 5})
        _score_http(r, "POST /search (Terraform)")
        if r["status_code"] == 200:
            results = r["body"].get("results", [])
            print(f"  ── Search Results for: \"{query}\" ──")
            print(f"  Matches: {len(results)}")
            for i, res in enumerate(results[:3]):
                print(f"    #{i+1}: score={res.get('score', 0):.4f} | "
                      f"{_truncate(str(res.get('text', '')), 100)}")

    def test_generate(self):
        prompt = "Deploy a 3-node Kubernetes cluster on AWS EKS with m5.large instances"
        r = _post("/generate", {
            "prompt": prompt,
            "max_new_tokens": 100,
            "temperature": 0.7,
        })
        _score_http(r, "POST /generate")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{prompt}\"")
            print(f"  ── Answer ──")
            answer = r["body"].get("generated_text") or r["body"].get("response", "")
            print(f"  {_truncate(str(answer), 300)}")
            print(f"  Model loaded: {r['body'].get('model_loaded')} | "
                  f"Device: {r['body'].get('device')}")

    def test_generate_provision_prompt(self):
        prompt = "Deploy EC2 instance with Docker"
        r = _post("/generate", {
            "prompt": prompt,
            "max_new_tokens": 150,
        })
        _score_http(r, "POST /generate (provision prompt)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{prompt}\"")
            print(f"  ── Answer ──")
            answer = r["body"].get("generated_text") or r["body"].get("response", "")
            print(f"  {_truncate(str(answer), 300)}")


# ============================================================================
# V1 RAG + REASONING
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestV1Endpoints:
    """V1 RAG + Reasoning endpoints."""

    def test_v1_query_provisioning(self):
        query = "Deploy a small EC2 instance with 30GB disk in us-east-1"
        r = _post("/api/models/v1/query", {
            "query": query,
            "include_reasoning": True,
            "top_k": 5,
        })
        _score_http(r, "V1 query (provisioning)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            reasoning = r["body"].get("reasoning", {})
            print(f"  ── Reasoning ──")
            print(f"  Intent: {reasoning.get('intent')}")
            print(f"  Confidence: {reasoning.get('confidence', 0):.2f}")
            print(f"  Context docs: {len(r['body'].get('context', []))}")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")

    def test_v1_query_troubleshooting(self):
        query = "My EKS pods keep crashing with OOM errors, how to fix?"
        r = _post("/api/models/v1/query", {
            "query": query,
            "include_reasoning": True,
            "top_k": 5,
        })
        _score_http(r, "V1 query (troubleshooting)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            reasoning = r["body"].get("reasoning", {})
            if reasoning:
                print(f"  Intent: {reasoning.get('intent')} | "
                      f"Confidence: {reasoning.get('confidence', 0):.2f}")

    def test_v1_query_no_reasoning(self):
        query = "What is Docker?"
        r = _post("/api/models/v1/query", {
            "query": query,
            "include_reasoning": False,
            "top_k": 3,
        })
        _score_http(r, "V1 query (no reasoning)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            assert "reasoning" not in r["body"] or r["body"].get("reasoning") is None

    def test_v1_developer_terraform(self):
        query = "Create a VPC with private subnets, NAT gateway, and flow logs"
        r = _post("/api/models/v1/developer", {
            "query": query,
            "include_code": True,
            "include_reasoning": True,
        })
        _score_http(r, "V1 developer (Terraform VPC)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            code_examples = r["body"].get("code_examples", [])
            print(f"  Code examples: {len(code_examples)}")
            for i, ex in enumerate(code_examples[:2]):
                snippet = _truncate(str(ex.get("code") or ex), 150)
                print(f"    [{i}] {snippet}")

    def test_v1_developer_no_code(self):
        query = "Explain Kubernetes networking"
        r = _post("/api/models/v1/developer", {
            "query": query,
            "include_code": False,
            "include_reasoning": True,
        })
        _score_http(r, "V1 developer (no code)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")

    def test_v1_terminal_kubectl(self):
        command = "kubectl get pods -n production showing CrashLoopBackOff"
        r = _post("/api/models/v1/terminal", {
            "command": command,
            "include_explanation": True,
        })
        _score_http(r, "V1 terminal (kubectl)")
        if r["status_code"] == 200:
            print(f"  ── Command Submitted ──")
            print(f"  \"{command}\"")
            explanation = (r["body"].get("explanation") or
                           r["body"].get("response") or
                           r["body"].get("answer", ""))
            if explanation:
                print(f"  ── Explanation ──")
                print(f"  {_truncate(str(explanation), 300)}")
            print(f"  Incidents: {len(r['body'].get('incidents', []))}")
            print(f"  Recommendations: {len(r['body'].get('recommendations', []))}")
            for i, rec in enumerate(r["body"].get("recommendations", [])[:3]):
                print(f"    [{i}] {_truncate(str(rec), 100)}")

    def test_v1_terminal_docker(self):
        command = "docker container keeps restarting with exit code 137"
        r = _post("/api/models/v1/terminal", {
            "command": command,
            "include_explanation": True,
        })
        _score_http(r, "V1 terminal (docker)")
        if r["status_code"] == 200:
            print(f"  ── Command Submitted ──")
            print(f"  \"{command}\"")
            explanation = (r["body"].get("explanation") or
                           r["body"].get("response") or
                           r["body"].get("answer", ""))
            if explanation:
                print(f"  ── Explanation ──")
                print(f"  {_truncate(str(explanation), 300)}")
            incidents = r["body"].get("incidents", [])
            if incidents:
                print(f"  Incidents: {len(incidents)}")
                for i, inc in enumerate(incidents[:2]):
                    print(f"    [{i}] {_truncate(str(inc), 100)}")


# ============================================================================
# V2 NLP + ENTITY EXTRACTION
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestV2Endpoints:
    """V2 NLP and entity extraction."""

    def test_v2_query_aws(self):
        query = "EC2 instance i-0abc123def in us-east-1 showing high CPU and connection timeout errors"
        r = _post("/api/models/v2/query", {
            "query": query,
            "extract_entities": True,
            "include_recommendations": True,
            "top_k": 5,
        })
        _score_http(r, "V2 NLP query (AWS)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            summary = r["body"].get("entity_summary", {})
            print(f"  ── Entities Extracted ──")
            print(f"  Total: {summary.get('total', 0)}")
            print(f"  Categories: {list(summary.get('by_category', {}).keys())}")
            recs = r["body"].get("recommendations", [])
            print(f"  ── Recommendations ({len(recs)}) ──")
            for i, rec in enumerate(recs[:3]):
                print(f"    [{i}] {_truncate(str(rec), 120)}")

    def test_v2_query_kubernetes(self):
        query = "EKS cluster pod deployment failing with OOM and rate limit errors"
        r = _post("/api/models/v2/query", {
            "query": query,
            "extract_entities": True,
            "include_recommendations": True,
        })
        _score_http(r, "V2 NLP query (K8s)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            recs = r["body"].get("recommendations", [])
            if recs:
                print(f"  Recommendations: {len(recs)}")

    def test_v2_extract_cloud_services(self):
        text = (
            "We use EKS with Terraform for IaC, Prometheus and Grafana for monitoring, "
            "Redis for caching, and FastAPI on port :8080 behind an nginx reverse proxy. "
            "Our CI/CD runs on GitHub Actions deploying to AWS us-west-2."
        )
        r = _post("/api/models/v2/extract", {"text": text})
        _score_http(r, "V2 extract (cloud stack)")
        if r["status_code"] == 200:
            print(f"  ── Input Text ──")
            print(f"  \"{_truncate(text, 200)}\"")
            summary = r["body"].get("summary", {})
            print(f"  ── Extraction Results ──")
            print(f"  Total entities: {summary.get('total_entities', 0)}")
            cloud = summary.get("cloud_services", [])
            print(f"  Cloud services: {cloud}")
            errors = summary.get("errors_detected", [])
            print(f"  Errors detected: {errors}")
            entities = r["body"].get("entities", [])
            if entities:
                print(f"  ── Entities Detail ({len(entities)}) ──")
                for i, ent in enumerate(entities[:5]):
                    print(f"    [{i}] {ent.get('label', '?')}: "
                          f"\"{ent.get('text', '')}\" (conf: {ent.get('confidence', 0):.2f})")

    def test_v2_extract_security(self):
        text = "Found XSS vulnerability in the API endpoint. Stack trace visible in production. JWT tokens not rotated."
        r = _post("/api/models/v2/extract", {
            "text": text,
            "entity_types": ["security_issues"],
        })
        _score_http(r, "V2 extract (security)")
        if r["status_code"] == 200:
            print(f"  ── Input Text ──")
            print(f"  \"{text}\"")
            entities = r["body"].get("entities", [])
            print(f"  ── Entities Found ({len(entities)}) ──")
            for i, ent in enumerate(entities[:5]):
                print(f"    [{i}] {ent.get('label', '?')}: "
                      f"\"{ent.get('text', '')}\"")

    def test_v2_extract_network(self):
        text = "Server 192.168.1.100 on port :3000 cannot reach database at 10.0.1.50:5432"
        r = _post("/api/models/v2/extract", {"text": text})
        _score_http(r, "V2 extract (network)")
        if r["status_code"] == 200:
            print(f"  ── Input Text ──")
            print(f"  \"{text}\"")
            entities = r["body"].get("entities", [])
            ip_entities = [e for e in entities if e.get("label") == "IP_ADDRESS"]
            port_entities = [e for e in entities if e.get("label") == "PORT"]
            print(f"  ── Entities Found ──")
            print(f"  IPs found: {len(ip_entities)}")
            for ip in ip_entities:
                print(f"    → {ip.get('text', '')}")
            print(f"  Ports found: {len(port_entities)}")
            for port in port_entities:
                print(f"    → {port.get('text', '')}")

    def test_v2_status(self):
        r = _get("/api/models/v2/status")
        _score_http(r, "V2 NLP status")
        if r["status_code"] == 200:
            print(f"  ── NLP Capabilities ──")
            caps = r["body"].get("capabilities", {})
            for name, info in caps.items():
                status = "available" if info.get("available") else "not available"
                print(f"    {name}: {status}")
            print(f"  Total patterns: {r['body'].get('total_patterns', 0)}")


# ============================================================================
# V3 INCIDENT PATTERNS
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestV3Endpoints:
    """V3 incident pattern analysis."""

    def test_v3_cloud_devops_incidents(self):
        query = "EKS node failures and pod evictions in us-east-1"
        r = _post("/api/models/v3/query", {
            "query": query,
            "top_k": 10,
            "include_reasoning": True,
            "focus": "cloud_devops",
        })
        _score_http(r, "V3 incidents (cloud_devops)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            metrics = r["body"].get("metrics", {})
            print(f"  ── Incident Metrics ──")
            print(f"  Total incidents: {metrics.get('total_incidents', 0)}")
            print(f"  Unusual: {metrics.get('unusual_count', 0)}")
            print(f"  Signals: {r['body'].get('signals_used', [])}")
            incidents = r["body"].get("incidents", [])
            if incidents:
                print(f"  ── Top Incidents ({len(incidents)}) ──")
                for i, inc in enumerate(incidents[:3]):
                    print(f"    [{i}] {_truncate(str(inc), 120)}")
            perf = r["body"].get("performance", {})
            if perf:
                print(f"  Processing time: {perf.get('total_ms', 0):.1f}ms")

    def test_v3_general_incidents(self):
        query = "Database connection pool exhaustion and slow queries"
        r = _post("/api/models/v3/query", {
            "query": query,
            "top_k": 5,
            "include_reasoning": True,
        })
        _score_http(r, "V3 incidents (general)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")
            metrics = r["body"].get("metrics", {})
            if metrics:
                print(f"  Total incidents: {metrics.get('total_incidents', 0)} | "
                      f"Unusual: {metrics.get('unusual_count', 0)}")

    def test_v3_no_reasoning(self):
        query = "API latency spikes"
        r = _post("/api/models/v3/query", {
            "query": query,
            "include_reasoning": False,
        })
        _score_http(r, "V3 incidents (no reasoning)")
        if r["status_code"] == 200:
            print(f"  ── Question Asked ──")
            print(f"  \"{query}\"")
            answer = r["body"].get("response") or r["body"].get("answer", "")
            if answer:
                print(f"  ── Answer ──")
                print(f"  {_truncate(str(answer), 300)}")


# ============================================================================
# CLOUD PROVISIONING
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestCloudProvisioning:
    """Cloud provisioning intent — all 6 types + edge cases."""

    def test_provision_vm_ec2(self):
        query = "Deploy EC2 instance t3.medium 50GB gp3 Ubuntu in us-west-2"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision VM (EC2)")
        self._validate_provision(r, query, "provisioning", "provision_vm",
                                 ["instance_type", "region", "cloud_provider"])

    def test_provision_kubernetes_eks(self):
        query = "Create an EKS cluster, 3 nodes, m5.large, kubernetes 1.29 in us-east-1"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision K8s (EKS)")
        self._validate_provision(r, query, "provisioning", "provision_kubernetes",
                                 ["cluster_name", "node_count", "node_type"])

    def test_provision_docker_nginx(self):
        query = "Run a nginx Docker container, port 80:80"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision Docker (nginx)")
        self._validate_provision(r, query, "provisioning", "provision_docker",
                                 ["docker_image", "ports"])

    def test_provision_database_postgres(self):
        query = "Deploy PostgreSQL database, version 16, name analytics_db, user admin"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision DB (PostgreSQL)")
        self._validate_provision(r, query, "provisioning", "provision_database",
                                 ["database_engine", "database_name"])

    def test_provision_fastapi_app(self):
        query = "Deploy FastAPI app billing-api, port 8000, http port 80"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision FastAPI")
        self._validate_provision(r, query, "provisioning", "provision_fastapi",
                                 ["app_name", "app_port"])

    def test_provision_static_website(self):
        query = "Deploy static website to nginx on docs.example.com, port 80"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision Static Website")
        self._validate_provision(r, query, "provisioning", "provision_static_website",
                                 ["server_name", "http_port"])

    def test_provision_empty_query(self):
        query = ""
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision empty query", expect_success=False)
        print(f"  ── Request ──")
        print(f"  Query: (empty string)")
        if r["status_code"] == 200:
            print(f"  ── Response ──")
            print(f"  query_type: {r['body'].get('query_type')}")
            assert r["body"].get("query_type") == "other"

    def test_provision_rds_mysql(self):
        query = "Deploy an RDS MySQL 8.0 instance, db.r5.large, 100GB storage, multi-AZ in us-east-1"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision DB (RDS MySQL)")
        self._validate_provision(r, query, "provisioning", "provision_database",
                                 ["database_engine", "region"])

    def test_provision_lambda_function(self):
        query = "Deploy an AWS Lambda function image-resizer, runtime python3.12, 512MB memory, 30s timeout"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision Lambda")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_s3_bucket(self):
        query = "Create an S3 bucket my-data-lake-prod with versioning enabled in eu-west-1"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision S3 Bucket")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")
            payload = body.get("payload") or {}
            if payload:
                print(f"  ── Extracted Payload ──")
                for k in sorted(payload.keys()):
                    v = payload[k]
                    if v and str(v).strip().lower() not in ("", "nan", "none"):
                        print(f"    {k}: {v}")

    def test_provision_gke_cluster(self):
        query = "Deploy a GKE cluster in us-central1, 5 nodes, n2-standard-4, kubernetes 1.28"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision K8s (GKE)")
        self._validate_provision(r, query, "provisioning", "provision_kubernetes",
                                 ["node_count", "node_type"])

    def test_provision_aks_cluster(self):
        query = "Create an AKS cluster my-aks in eastus, 3 nodes, Standard_D4s_v3"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision K8s (AKS)")
        self._validate_provision(r, query, "provisioning", "provision_kubernetes",
                                 ["cluster_name", "node_count"])

    def test_provision_redis_container(self):
        query = "Run a Redis Docker container on port 6379:6379 with persistent volume"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision Docker (Redis)")
        self._validate_provision(r, query, "provisioning", "provision_docker",
                                 ["docker_image", "ports"])

    # -- IAM / Security intent tests --

    def test_provision_iam_role_ec2(self):
        query = "Create an IAM role for EC2 instances with S3 read access"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision IAM Role (EC2+S3)")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_iam_role_lambda(self):
        query = "Create an IAM role for Lambda execution with DynamoDB access"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision IAM Role (Lambda)")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_iam_policy(self):
        query = "Create an IAM policy for custom S3 bucket access to my-data-bucket"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision IAM Policy (S3)")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_iam_user(self):
        query = "Create an IAM user for CI/CD pipeline with programmatic access"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision IAM User (CI/CD)")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_gcp_service_account(self):
        query = "Create a GCP service account for Cloud Storage access"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision GCP Service Account")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_keypair(self):
        query = "Create an SSH key pair for production EC2 instances"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision SSH Key Pair")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    # -- Networking intent tests --

    def test_provision_vpc(self):
        query = "Create a VPC with CIDR 10.0.0.0/16 and NAT gateway in us-east-1"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision VPC")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_subnet(self):
        query = "Create a private subnet 10.0.10.0/24 in us-east-1b for the database tier"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision Subnet")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_security_group(self):
        query = "Create a security group allowing SSH, HTTP, and HTTPS from anywhere"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision Security Group")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_load_balancer(self):
        query = "Create an Application Load Balancer with target group on port 80 and health check"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision ALB")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_vpc_peering(self):
        query = "Create a VPC peering connection between prod and staging VPCs"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision VPC Peering")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_vpn_gateway(self):
        query = "Create a VPN gateway with IPSec tunnel to on-premise datacenter"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision VPN Gateway")
        if r["status_code"] == 200:
            body = r["body"]
            print(f"  ── Request ──")
            print(f"  Query: \"{query}\"")
            print(f"  ── Classification ──")
            print(f"  query_type={body.get('query_type')} intent={body.get('intent')} "
                  f"confidence={body.get('confidence', 0):.4f}")

    def test_provision_non_cloud_query(self):
        query = "What is the capital of France?"
        r = _post("/api/cloud/provision-intent", {"query": query})
        _score_http(r, "Provision non-cloud query", expect_success=False)
        print(f"  ── Request ──")
        print(f"  Query: \"{query}\"")
        if r["status_code"] in (200, 400, 422):
            print(f"  ── Response ──")
            print(f"  query_type: {r['body'].get('query_type')}")
            print(f"  intent: {r['body'].get('intent')}")

    def _validate_provision(self, r, query: str, expected_qt: str,
                            expected_intent: str, expected_keys: list):
        if r["status_code"] != 200:
            return
        body = r["body"]
        qt = body.get("query_type")
        intent = body.get("intent")
        confidence = body.get("confidence", 0)
        payload = body.get("payload") or {}

        print(f"  ── Request ──")
        print(f"  Query: \"{query}\"")
        print(f"  ── Classification ──")
        print(f"  query_type={qt} intent={intent} confidence={confidence:.4f}")

        if qt != expected_qt:
            print(f"  ⚠ WARNING: query_type expected '{expected_qt}', got '{qt}'")
        if intent != expected_intent:
            print(f"  ⚠ WARNING: intent expected '{expected_intent}', got '{intent}'")
        for key in expected_keys:
            if key not in payload:
                print(f"  ⚠ WARNING: payload missing '{key}'")

        if payload:
            print(f"  ── Extracted Payload ──")
            for k in sorted(payload.keys()):
                v = payload[k]
                if v and str(v).strip().lower() not in ("", "nan", "none"):
                    print(f"    {k}: {v}")
        answer = body.get("response") or body.get("answer", "")
        if answer:
            print(f"  ── Response ──")
            print(f"  {_truncate(str(answer), 300)}")


# ============================================================================
# STANDALONE RUNNER
# ============================================================================

if __name__ == "__main__":
    print(__doc__)
    print("=" * 70)
    print(f"  Target API: {BASE_URL}")
    print(f"  Timestamp:  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    print("\nRunning tests with pytest...\n")
    sys.exit(pytest.main([__file__, "-v", "-s", "--tb=short"]))
