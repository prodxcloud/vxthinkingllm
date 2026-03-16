"""
VaLLM Interactive Chat & LLM Generation Tests
===============================================

Author: Joel Otepa Wembo
https://joelwembo.com

DESCRIPTION
===========
Multi-turn conversational test suite that talks to VaLLM like a real user
would interact with ChatGPT, Claude, or OpenAI.  Tests exercise:

    MODE 1 — Automated Chat Conversations (scored)
    ================================================
    Runs pre-defined multi-turn conversations against the API, scoring each
    response for relevance, coherence, and correctness.  Covers:

      - Cloud infrastructure Q&A (multi-turn follow-ups)
      - Provisioning workflows (ask → clarify → deploy)
      - Troubleshooting dialogues (symptom → diagnosis → fix)
      - DevOps knowledge queries (Terraform, K8s, Docker)
      - LLM text generation quality (8 prompts, scored 0-100)

    MODE 2 — Live Interactive Chat (terminal REPL)
    ================================================
    Open a terminal chat session and talk to VaLLM freely.  Auto-routes
    queries to the best endpoint.  Supports conversation memory.

    MODE 3 — Direct LLM Generation Tests (no server needed)
    ========================================================
    Loads the fine-tuned model from disk and tests text generation
    quality with cloud/DevOps prompts.

USAGE
=====
    # Start the app first (for API modes):
    uvicorn app.app:app --host 0.0.0.0 --port 8746

    # Run automated conversation tests (needs server)
    python -m app.tests.tests_interactive_chat

    # Run with pytest (scored tests only)
    pytest app/tests/tests_interactive_chat.py -v -s

    # Start live interactive chat
    python -m app.tests.tests_interactive_chat --interactive

    # Run direct LLM generation tests (no server needed)
    python -m app.tests.tests_interactive_chat --generate

    # Custom URL
    python -m app.tests.tests_interactive_chat --url http://localhost:8746
"""

import atexit
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

BASE_URL = os.environ.get("VALLM_TEST_URL", "http://localhost:8746")


# ============================================================================
# SCORECARD
# ============================================================================

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
    print("  VALLM INTERACTIVE CHAT - FINAL SCORECARD")
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
# CHAT CLIENT — stateful conversation with memory
# ============================================================================

class VaLLMChatClient:
    """Stateful chat client that maintains conversation history."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session_id = str(uuid.uuid4())
        self.history: List[Dict[str, str]] = []
        self.turn = 0

    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def _build_context_prompt(self, user_message: str) -> str:
        """Build a prompt that includes recent conversation history."""
        if not self.history:
            return user_message
        context_parts = []
        for entry in self.history[-6:]:
            role = entry["role"]
            content = entry["content"][:300]
            context_parts.append(f"{role}: {content}")
        context_parts.append(f"User: {user_message}")
        return "\n".join(context_parts)

    def chat(self, message: str, endpoint: str = "auto", timeout: float = 60.0) -> Dict[str, Any]:
        """Send a message and get a response.  Supports multiple endpoints."""
        self.turn += 1
        self.history.append({"role": "User", "content": message})

        start = time.perf_counter()

        if endpoint == "auto":
            endpoint = self._auto_route(message)

        try:
            if endpoint == "generate":
                context_prompt = self._build_context_prompt(message)
                r = self.session.post(f"{self.base_url}/generate", json={
                    "prompt": context_prompt,
                    "max_new_tokens": 200,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }, timeout=timeout)
                data = r.json()
                response_text = data.get("response", data.get("text", ""))
                result = {
                    "endpoint": "/generate",
                    "status_code": r.status_code,
                    "response": response_text,
                    "model_loaded": data.get("model_loaded", False),
                    "device": data.get("device", "unknown"),
                }

            elif endpoint == "v1_query":
                r = self.session.post(f"{self.base_url}/api/models/v1/query", json={
                    "query": message,
                    "include_reasoning": True,
                    "top_k": 5,
                }, timeout=timeout)
                data = r.json()
                reasoning = data.get("reasoning", {})
                result = {
                    "endpoint": "/api/models/v1/query",
                    "status_code": r.status_code,
                    "response": data.get("response", ""),
                    "intent": reasoning.get("intent"),
                    "confidence": reasoning.get("confidence", 0),
                    "steps": len(reasoning.get("steps", [])),
                    "context_docs": len(data.get("context", [])),
                }

            elif endpoint == "v1_developer":
                r = self.session.post(f"{self.base_url}/api/models/v1/developer", json={
                    "query": message,
                    "include_code": True,
                    "include_reasoning": True,
                }, timeout=timeout)
                data = r.json()
                result = {
                    "endpoint": "/api/models/v1/developer",
                    "status_code": r.status_code,
                    "response": data.get("response", ""),
                    "code_examples": len(data.get("code_examples", [])),
                }

            elif endpoint == "provision":
                r = self.session.post(f"{self.base_url}/api/cloud/provision-intent", json={
                    "query": message,
                }, timeout=timeout)
                data = r.json()
                result = {
                    "endpoint": "/api/cloud/provision-intent",
                    "status_code": r.status_code,
                    "response": f"Intent: {data.get('intent')} | Confidence: {data.get('confidence', 0):.2f}",
                    "query_type": data.get("query_type"),
                    "intent": data.get("intent"),
                    "confidence": data.get("confidence", 0),
                    "payload": data.get("payload"),
                }

            elif endpoint == "v2_query":
                r = self.session.post(f"{self.base_url}/api/models/v2/query", json={
                    "query": message,
                    "extract_entities": True,
                    "include_recommendations": True,
                }, timeout=timeout)
                data = r.json()
                result = {
                    "endpoint": "/api/models/v2/query",
                    "status_code": r.status_code,
                    "response": data.get("response", ""),
                    "entities": len(data.get("entities", [])),
                    "recommendations": data.get("recommendations", []),
                }

            else:
                result = {"endpoint": "unknown", "status_code": 0, "response": "Unknown endpoint"}

        except Exception as e:
            result = {"endpoint": endpoint, "status_code": 0, "response": f"Error: {e}"}

        elapsed_ms = (time.perf_counter() - start) * 1000
        result["elapsed_ms"] = elapsed_ms
        result["turn"] = self.turn

        response_text = result.get("response", "")
        self.history.append({"role": "Assistant", "content": response_text[:500]})

        return result

    def _auto_route(self, message: str) -> str:
        """Auto-route message to the best endpoint."""
        m = message.lower()
        provision_kw = [
            "deploy", "provision", "create", "launch", "spin up", "set up",
            "ec2", "instance", "vm", "server", "kubernetes", "eks", "aks", "gke",
            "cluster", "docker", "container", "database", "postgres", "mysql",
            "fastapi", "website", "static site", "nginx",
            "iam", "role", "policy", "user", "service account", "keypair", "key pair",
            "secret", "cloudtrail",
            "vpc", "subnet", "security group", "load balancer", "alb", "nlb",
            "elastic ip", "route table", "nat gateway", "vpn", "peering",
            "transit gateway", "dns record", "acl", "firewall", "nsg", "vnet",
        ]
        if sum(1 for kw in provision_kw if kw in m) >= 2:
            return "provision"

        dev_kw = ["terraform", "code", "write", "script", "yaml", "dockerfile", "helm chart", "iac"]
        if any(kw in m for kw in dev_kw):
            return "v1_developer"

        nlp_kw = ["extract", "entities", "analyze text", "what services"]
        if any(kw in m for kw in nlp_kw):
            return "v2_query"

        return "v1_query"

    def reset(self):
        """Reset conversation state."""
        self.history.clear()
        self.turn = 0
        self.session_id = str(uuid.uuid4())


# ============================================================================
# CONVERSATION DEFINITIONS — multi-turn scored dialogues
# ============================================================================

CONVERSATIONS: List[Dict[str, Any]] = [
    {
        "id": "CONV-1",
        "name": "Cloud Infrastructure Q&A",
        "description": "Ask about cloud concepts, then follow up with details",
        "turns": [
            {
                "user": "What is Kubernetes and why do companies use it?",
                "endpoint": "v1_query",
                "check_keywords": ["kubernetes", "container", "orchestr"],
                "expect_response": True,
            },
            {
                "user": "How does it compare to Docker Swarm?",
                "endpoint": "v1_query",
                "check_keywords": ["docker", "swarm"],
                "expect_response": True,
            },
            {
                "user": "What about scaling — can Kubernetes auto-scale?",
                "endpoint": "v1_query",
                "check_keywords": ["scal"],
                "expect_response": True,
            },
        ],
    },
    {
        "id": "CONV-2",
        "name": "Provisioning Workflow",
        "description": "User asks to deploy, system resolves intent and payload",
        "turns": [
            {
                "user": "I need to deploy a web server on AWS",
                "endpoint": "provision",
                "check_intent": "provision_vm",
                "expect_response": True,
            },
            {
                "user": "Make it a t3.medium instance with 50GB storage in us-west-2",
                "endpoint": "provision",
                "check_intent": "provision_vm",
                "check_payload_keys": ["instance_type", "region"],
                "expect_response": True,
            },
            {
                "user": "Also set up an EKS cluster with 3 nodes in the same region",
                "endpoint": "provision",
                "check_intent": "provision_kubernetes",
                "expect_response": True,
            },
            {
                "user": "And deploy a PostgreSQL database named app_db",
                "endpoint": "provision",
                "check_intent": "provision_database",
                "expect_response": True,
            },
        ],
    },
    {
        "id": "CONV-3",
        "name": "Troubleshooting Dialogue",
        "description": "User reports a problem, system diagnoses and recommends fixes",
        "turns": [
            {
                "user": "My EKS pods keep crashing with OOM errors, what should I check?",
                "endpoint": "v1_query",
                "check_keywords": ["memory", "resource", "limit"],
                "expect_response": True,
            },
            {
                "user": "I already increased limits to 2Gi but it still crashes",
                "endpoint": "v1_query",
                "expect_response": True,
            },
            {
                "user": "Could it be a memory leak in the application itself?",
                "endpoint": "v1_query",
                "expect_response": True,
            },
        ],
    },
    {
        "id": "CONV-4",
        "name": "DevOps Code Generation",
        "description": "User asks for infrastructure-as-code, gets Terraform/configs",
        "turns": [
            {
                "user": "Write me a Terraform config for a VPC with private subnets and NAT gateway",
                "endpoint": "v1_developer",
                "check_keywords": ["terraform", "vpc", "subnet"],
                "expect_code": True,
                "expect_response": True,
            },
            {
                "user": "Now add VPC flow logs with CloudWatch",
                "endpoint": "v1_developer",
                "check_keywords": ["flow", "log"],
                "expect_response": True,
            },
        ],
    },
    {
        "id": "CONV-5",
        "name": "NLP Entity Analysis Chat",
        "description": "User describes infrastructure, system extracts entities",
        "turns": [
            {
                "user": "We run EKS with Terraform, use Prometheus and Grafana for monitoring, Redis for caching, and FastAPI behind nginx",
                "endpoint": "v2_query",
                "check_entity_count": 3,
                "expect_response": True,
            },
            {
                "user": "We also have connection timeout errors and high CPU on our EC2 instances in us-east-1",
                "endpoint": "v2_query",
                "check_entity_count": 2,
                "expect_response": True,
            },
        ],
    },
    {
        "id": "CONV-6",
        "name": "LLM Direct Generation",
        "description": "Talk to the fine-tuned LLM model directly via /generate",
        "turns": [
            {
                "user": "Explain how to deploy a Docker container on AWS ECS step by step",
                "endpoint": "generate",
                "expect_response": True,
                "min_word_count": 5,
            },
            {
                "user": "How do I configure auto-scaling for ECS tasks based on CPU usage?",
                "endpoint": "generate",
                "expect_response": True,
                "min_word_count": 5,
            },
            {
                "user": "Can you also explain the difference between ECS and EKS?",
                "endpoint": "generate",
                "expect_response": True,
                "min_word_count": 5,
            },
        ],
    },
    {
        "id": "CONV-7",
        "name": "IAM & Network Provisioning",
        "description": "User provisions IAM roles and networking resources",
        "turns": [
            {
                "user": "Create an IAM role for my EC2 instances to access S3 buckets",
                "endpoint": "provision",
                "expect_response": True,
            },
            {
                "user": "Also create a VPC with CIDR 10.0.0.0/16 and NAT gateway in us-east-1",
                "endpoint": "provision",
                "expect_response": True,
            },
            {
                "user": "Now set up a security group allowing SSH and HTTPS from anywhere",
                "endpoint": "provision",
                "expect_response": True,
            },
            {
                "user": "Deploy an Application Load Balancer with target group on port 443",
                "endpoint": "provision",
                "expect_response": True,
            },
        ],
    },
]


# ============================================================================
# LLM GENERATION TEST PROMPTS (no server needed)
# ============================================================================

GENERATION_PROMPTS = [
    {
        "id": "G1",
        "name": "Cloud Architecture Explanation",
        "prompt": "Explain a three-tier architecture on AWS with VPC, load balancer, EC2, and RDS.",
        "max_tokens": 150,
        "keywords": ["vpc", "load", "ec2", "rds", "tier"],
    },
    {
        "id": "G2",
        "name": "Kubernetes Troubleshooting",
        "prompt": "A Kubernetes pod is in CrashLoopBackOff. What are the common causes and how to debug?",
        "max_tokens": 150,
        "keywords": ["pod", "crash", "log", "debug", "container"],
    },
    {
        "id": "G3",
        "name": "Terraform Best Practices",
        "prompt": "What are best practices for organizing Terraform code in a large project?",
        "max_tokens": 150,
        "keywords": ["module", "state", "terraform", "variable"],
    },
    {
        "id": "G4",
        "name": "Docker Security",
        "prompt": "How to secure a Docker container in production? List the key security measures.",
        "max_tokens": 150,
        "keywords": ["docker", "security", "image", "root"],
    },
    {
        "id": "G5",
        "name": "CI/CD Pipeline Design",
        "prompt": "Design a CI/CD pipeline for a FastAPI application using GitHub Actions and AWS ECS.",
        "max_tokens": 200,
        "keywords": ["github", "action", "deploy", "test", "pipeline"],
    },
    {
        "id": "G6",
        "name": "Cost Optimization",
        "prompt": "What are the top 5 ways to reduce AWS cloud costs for a mid-size company?",
        "max_tokens": 150,
        "keywords": ["cost", "reserved", "spot", "right-siz"],
    },
    {
        "id": "G7",
        "name": "Incident Response",
        "prompt": "An RDS database is showing high CPU and slow queries in production. What is the incident response process?",
        "max_tokens": 150,
        "keywords": ["cpu", "query", "rds", "database", "performance"],
    },
    {
        "id": "G8",
        "name": "Multi-Turn Context",
        "prompt": "I previously deployed an EKS cluster with 3 nodes. Now I want to add a Redis cache and an RDS PostgreSQL database to the same VPC. What is the recommended setup?",
        "max_tokens": 180,
        "keywords": ["redis", "rds", "vpc", "cluster", "database"],
    },
    {
        "id": "G9",
        "name": "IAM Role Design",
        "prompt": "How do I create an IAM role for Lambda functions that need access to DynamoDB and S3? Explain the trust policy and permissions.",
        "max_tokens": 180,
        "keywords": ["iam", "role", "lambda", "policy", "trust"],
    },
    {
        "id": "G10",
        "name": "VPC Network Architecture",
        "prompt": "Design a VPC with public and private subnets, NAT gateway, and security groups for a 3-tier web application on AWS.",
        "max_tokens": 200,
        "keywords": ["vpc", "subnet", "nat", "security", "tier"],
    },
]


# ============================================================================
# SCORING HELPERS
# ============================================================================

def score_turn(turn_def: dict, result: dict) -> int:
    """Score a single conversation turn (1-10)."""
    score = 1
    details = []

    if result.get("status_code") != 200:
        details.append(f"HTTP {result.get('status_code')}")
        return 2

    score = 4

    response = result.get("response", "")
    if not response or len(response.strip()) < 5:
        details.append("empty response")
        return 3

    score = 5

    if result.get("elapsed_ms", 99999) < 5000:
        score += 1
    if result.get("elapsed_ms", 99999) < 2000:
        score += 1

    keywords = turn_def.get("check_keywords", [])
    if keywords:
        response_lower = response.lower()
        matched = [kw for kw in keywords if kw in response_lower]
        if len(matched) >= len(keywords):
            score += 2
        elif matched:
            score += 1
        else:
            details.append(f"missing keywords: {keywords}")

    expected_intent = turn_def.get("check_intent")
    if expected_intent:
        actual = result.get("intent")
        if actual == expected_intent:
            score += 1
        else:
            details.append(f"intent: expected '{expected_intent}', got '{actual}'")

    payload_keys = turn_def.get("check_payload_keys", [])
    if payload_keys:
        payload = result.get("payload") or {}
        missing = [k for k in payload_keys if k not in payload]
        if not missing:
            score += 1
        else:
            details.append(f"payload missing: {missing}")

    min_entities = turn_def.get("check_entity_count", 0)
    if min_entities:
        actual_count = result.get("entities", 0)
        if actual_count >= min_entities:
            score += 1
        else:
            details.append(f"entities: expected >= {min_entities}, got {actual_count}")

    min_words = turn_def.get("min_word_count", 0)
    if min_words:
        word_count = len(response.split())
        if word_count >= min_words:
            score += 1
        else:
            details.append(f"too short: {word_count} words (expected >= {min_words})")

    return min(score, 10)


def score_generation_quality(text: str, prompt_def: dict) -> Dict[str, Any]:
    """Score LLM generation output quality (0-100 scale)."""
    score = 0
    details = []

    if not text or len(text.strip()) < 5:
        return {"score": 0, "pct": 0, "grade": "VERY POOR", "details": "empty output"}

    text_stripped = text.strip()
    word_count = len(text_stripped.split())

    # Non-empty (15 pts)
    score += 10
    if len(text_stripped) > 20:
        score += 5

    # Length (15 pts)
    if word_count >= 30:
        score += 15
    elif word_count >= 10:
        score += 10
    elif word_count >= 5:
        score += 5
    else:
        details.append(f"too short ({word_count} words)")

    # Keyword relevance (25 pts)
    keywords = prompt_def.get("keywords", [])
    if keywords:
        text_lower = text_stripped.lower()
        matched = [kw for kw in keywords if kw in text_lower]
        kw_score = round(len(matched) / len(keywords) * 25)
        score += kw_score
        if len(matched) < len(keywords) * 0.4:
            details.append(f"low keyword match ({len(matched)}/{len(keywords)})")

    # No error markers (10 pts)
    error_markers = ["error", "exception", "traceback", "failed"]
    if not any(m in text_stripped.lower() for m in error_markers):
        score += 10
    else:
        details.append("contains error markers")

    # Coherence — multiple sentences (15 pts)
    sentences = [s.strip() for s in text_stripped.split(".") if len(s.strip()) > 3]
    if len(sentences) >= 3:
        score += 15
    elif len(sentences) >= 2:
        score += 10
    elif len(sentences) >= 1:
        score += 5
    else:
        details.append("no sentence structure")

    # Not just repeating the prompt (10 pts)
    prompt_text = prompt_def.get("prompt", "")
    if text_stripped != prompt_text and not text_stripped.startswith(prompt_text):
        score += 10
    else:
        details.append("output is just the prompt repeated")

    pct = round(min(score, 100), 1)
    grade = (
        "EXCELLENT" if pct >= 85 else "GOOD" if pct >= 70 else
        "FAIR" if pct >= 50 else "POOR" if pct >= 30 else "VERY POOR"
    )
    return {
        "score": score, "pct": pct, "grade": grade, "word_count": word_count,
        "details": "; ".join(details) if details else "Good generation",
    }


# ============================================================================
# PYTEST TESTS — automated conversation scoring
# ============================================================================

if HAS_PYTEST:

    @pytest.fixture(scope="module")
    def chat_client():
        client = VaLLMChatClient(BASE_URL)
        if not client.health_check():
            pytest.skip(f"VaLLM server not available at {BASE_URL}")
        return client

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation1_CloudQA:
        """Multi-turn cloud infrastructure Q&A."""

        def test_turn1_what_is_k8s(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[0]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])
            print(f"  Response: {result.get('response', '')[:200]}...")

        def test_turn2_vs_swarm(self, chat_client):
            conv = CONVERSATIONS[0]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])

        def test_turn3_autoscale(self, chat_client):
            conv = CONVERSATIONS[0]
            turn = conv["turns"][2]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 3", s, turn["user"][:50])

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation2_Provisioning:
        """Multi-turn provisioning workflow."""

        def test_turn1_deploy_web_server(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[1]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])

        def test_turn2_specify_instance(self, chat_client):
            conv = CONVERSATIONS[1]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])
            if result.get("payload"):
                for k, v in sorted(result["payload"].items()):
                    if v and str(v).strip().lower() not in ("", "nan", "none"):
                        print(f"    {k}: {v}")

        def test_turn3_add_eks(self, chat_client):
            conv = CONVERSATIONS[1]
            turn = conv["turns"][2]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 3", s, turn["user"][:50])

        def test_turn4_add_database(self, chat_client):
            conv = CONVERSATIONS[1]
            turn = conv["turns"][3]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 4", s, turn["user"][:50])

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation3_Troubleshooting:
        """Multi-turn troubleshooting dialogue."""

        def test_turn1_oom_error(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[2]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])

        def test_turn2_followup(self, chat_client):
            conv = CONVERSATIONS[2]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])

        def test_turn3_memory_leak(self, chat_client):
            conv = CONVERSATIONS[2]
            turn = conv["turns"][2]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 3", s, turn["user"][:50])

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation4_DevOps:
        """DevOps code generation dialogue."""

        def test_turn1_terraform_vpc(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[3]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])

        def test_turn2_add_flow_logs(self, chat_client):
            conv = CONVERSATIONS[3]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation5_NLP:
        """NLP entity extraction dialogue."""

        def test_turn1_describe_stack(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[4]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])

        def test_turn2_report_errors(self, chat_client):
            conv = CONVERSATIONS[4]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation7_IAMNetwork:
        """Multi-turn IAM & networking provisioning."""

        def test_turn1_iam_role(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[6]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])

        def test_turn2_vpc(self, chat_client):
            conv = CONVERSATIONS[6]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])

        def test_turn3_security_group(self, chat_client):
            conv = CONVERSATIONS[6]
            turn = conv["turns"][2]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 3", s, turn["user"][:50])

        def test_turn4_load_balancer(self, chat_client):
            conv = CONVERSATIONS[6]
            turn = conv["turns"][3]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 4", s, turn["user"][:50])

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    class TestConversation6_LLMGeneration:
        """Direct LLM /generate endpoint — multi-turn."""

        def test_turn1_deploy_ecs(self, chat_client):
            chat_client.reset()
            conv = CONVERSATIONS[5]
            turn = conv["turns"][0]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 1", s, turn["user"][:50])
            print(f"  Model loaded: {result.get('model_loaded')}")

        def test_turn2_autoscaling(self, chat_client):
            conv = CONVERSATIONS[5]
            turn = conv["turns"][1]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 2", s, turn["user"][:50])

        def test_turn3_ecs_vs_eks(self, chat_client):
            conv = CONVERSATIONS[5]
            turn = conv["turns"][2]
            result = chat_client.chat(turn["user"], turn["endpoint"])
            s = score_turn(turn, result)
            _record_score(f"{conv['name']} — Turn 3", s, turn["user"][:50])


# ============================================================================
# MODE 1 — AUTOMATED CONVERSATIONS (standalone runner)
# ============================================================================

def run_automated_conversations(base_url: str = BASE_URL):
    """Run all pre-defined conversations and produce a scorecard."""
    print("\n" + "=" * 78)
    print("  VaLLM Interactive Chat Tests - Automated Conversations")
    print("=" * 78)
    print(f"  Base URL:      {base_url}")
    print(f"  Conversations: {len(CONVERSATIONS)}")
    print(f"  Total turns:   {sum(len(c['turns']) for c in CONVERSATIONS)}")
    print("=" * 78)

    client = VaLLMChatClient(base_url)

    print("\nChecking service health...", end=" ")
    if not client.health_check():
        print("FAILED")
        print(f"\nService not available at {base_url}. Start the app first:")
        print("  uvicorn app.app:app --host 0.0.0.0 --port 8746")
        return
    print("OK\n")

    total_passed = 0
    total_turns = 0

    for conv in CONVERSATIONS:
        client.reset()
        print(f"\n{'=' * 78}")
        print(f"  CONVERSATION: {conv['name']}")
        print(f"  {conv['description']}")
        print(f"{'=' * 78}")

        for i, turn in enumerate(conv["turns"], 1):
            total_turns += 1
            print(f"\n  [{i}/{len(conv['turns'])}] User: {turn['user']}")

            result = client.chat(turn["user"], turn["endpoint"])
            response = result.get("response", "")
            elapsed = result.get("elapsed_ms", 0)

            print(f"  [{result.get('endpoint')}] {elapsed:.0f}ms")

            if result.get("status_code") == 200 and response:
                preview = response[:250].replace("\n", " ")
                print(f"  Assistant: {preview}...")
                total_passed += 1

                if result.get("intent"):
                    print(f"  Intent: {result['intent']} (confidence: {result.get('confidence', 0):.2f})")
                if result.get("code_examples"):
                    print(f"  Code examples: {result['code_examples']}")
                if result.get("entities"):
                    print(f"  Entities found: {result['entities']}")
            else:
                print(f"  [ERROR] Status {result.get('status_code')}: {response[:100]}")

    print(f"\n{'=' * 78}")
    print(f"  RESULTS: {total_passed}/{total_turns} turns successful")
    print(f"  Pass Rate: {total_passed / total_turns * 100:.0f}%")
    print(f"{'=' * 78}")


# ============================================================================
# MODE 2 — LIVE INTERACTIVE CHAT (terminal REPL)
# ============================================================================

def interactive_chat(base_url: str = BASE_URL, initial_query: str = ""):
    """Live interactive chat with VaLLM."""
    print("\n" + "=" * 78)
    print("  VaLLM Interactive Chat")
    print("=" * 78)
    print("  Talk to VaLLM like ChatGPT.  Your queries auto-route to the")
    print("  best endpoint.  Conversation history is maintained.")
    print()
    print("  Prefixes (force endpoint):")
    print("    /gen       Force /generate (raw LLM)")
    print("    /rag       Force V1 RAG query")
    print("    /dev       Force V1 developer (code)")
    print("    /cloud     Force cloud provisioning")
    print("    /nlp       Force V2 NLP analysis")
    print()
    print("  Commands:")
    print("    /reset     Clear conversation history")
    print("    /history   Show conversation history")
    print("    /health    Check service health")
    print("    /tests     Run automated conversation tests")
    print("    /quit      Exit")
    print("=" * 78)

    client = VaLLMChatClient(base_url)

    print(f"\n  Connecting to {base_url}...", end=" ")
    if not client.health_check():
        print("FAILED")
        print("  Start the app first: uvicorn app.app:app --host 0.0.0.0 --port 8746")
        return
    print("OK")

    if initial_query:
        client.turn += 1
        print(f"\n{'=' * 78}")
        print(f"  [{client.turn}] You: {initial_query}")
        endpoint = "auto"
        result = client.chat(initial_query, endpoint)
        _display_chat_result(result)

    while True:
        try:
            print()
            prompt = "  You > " if client.turn > 0 else "  Ask me anything > "
            user_input = input(prompt).strip()
            if not user_input:
                continue

            lower = user_input.lower()
            if lower in ("/quit", "/exit", "quit", "exit", "q"):
                print(f"\n  Session ended. {client.turn} messages exchanged. Goodbye!")
                break
            if lower == "/reset":
                client.reset()
                print("  Conversation history cleared.")
                continue
            if lower == "/history":
                if not client.history:
                    print("  No history yet.")
                else:
                    for entry in client.history:
                        role = entry["role"]
                        content = entry["content"][:120]
                        print(f"    {role}: {content}...")
                continue
            if lower == "/health":
                status = "OK" if client.health_check() else "Unreachable"
                print(f"  Health: {status}")
                continue
            if lower == "/tests":
                run_automated_conversations(base_url)
                continue

            endpoint = "auto"
            if user_input.startswith("/gen "):
                user_input = user_input[5:]
                endpoint = "generate"
            elif user_input.startswith("/rag "):
                user_input = user_input[5:]
                endpoint = "v1_query"
            elif user_input.startswith("/dev "):
                user_input = user_input[5:]
                endpoint = "v1_developer"
            elif user_input.startswith("/cloud "):
                user_input = user_input[7:]
                endpoint = "provision"
            elif user_input.startswith("/nlp "):
                user_input = user_input[5:]
                endpoint = "v2_query"

            print(f"\n{'=' * 78}")
            print(f"  [{client.turn + 1}] You: {user_input}")
            result = client.chat(user_input, endpoint)
            _display_chat_result(result)

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  Session ended. {client.turn} messages exchanged. Goodbye!")
            break
        except Exception as e:
            print(f"  Error: {e}")


def _display_chat_result(result: dict):
    """Pretty-print a chat response."""
    endpoint = result.get("endpoint", "?")
    elapsed = result.get("elapsed_ms", 0)
    print(f"  [{endpoint}] {elapsed:.0f}ms")

    response = result.get("response", "")
    if not response:
        print("  (no response)")
        return

    print(f"\n  Assistant:")
    for line in response[:1200].split("\n"):
        print(f"    {line}")
    if len(response) > 1200:
        print(f"    ... ({len(response)} chars total)")

    if result.get("intent"):
        print(f"\n  Intent: {result['intent']} | Confidence: {result.get('confidence', 0):.2f}")
    if result.get("payload"):
        payload = result["payload"]
        relevant = {k: v for k, v in payload.items()
                    if v and str(v).strip().lower() not in ("", "nan", "none")}
        if relevant:
            print(f"  Payload:")
            for k, v in sorted(relevant.items()):
                print(f"    {k}: {v}")
    if result.get("code_examples"):
        print(f"  Code examples: {result['code_examples']}")
    if result.get("entities"):
        print(f"  Entities extracted: {result['entities']}")
    if result.get("recommendations"):
        print(f"  Recommendations:")
        for rec in result["recommendations"][:3]:
            print(f"    - {rec[:80]}")


# ============================================================================
# MODE 3 — DIRECT LLM GENERATION (no server needed)
# ============================================================================

def run_generation_tests():
    """Test the fine-tuned LLM model directly (no server)."""
    print("\n" + "=" * 78)
    print("  VaLLM LLM Generation Tests (direct model, no server)")
    print("=" * 78)

    MODEL_DIR = Path(__file__).parent.parent / "data" / "models"

    if not MODEL_DIR.exists() or not (MODEL_DIR / "config.json").exists():
        print(f"\n  Model not found at {MODEL_DIR}")
        print("  Train first: python -m app.services.ai.ml.train --num-train-epochs 1")
        return

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
    except ImportError:
        print("\n  Missing dependencies: pip install transformers torch")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Model dir: {MODEL_DIR}")
    print(f"  Device:    {device}")
    print(f"  Prompts:   {len(GENERATION_PROMPTS)}")

    print("\n  Loading model...", end=" ")
    start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    model = AutoModelForCausalLM.from_pretrained(str(MODEL_DIR)).to(device)
    load_ms = (time.perf_counter() - start) * 1000
    print(f"OK ({load_ms:.0f}ms)")

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {total_params:,}")
    print(f"  Vocab size: {tokenizer.vocab_size}")
    print("=" * 78)

    all_scores = []

    for prompt_def in GENERATION_PROMPTS:
        print(f"\n  [{prompt_def['id']}] {prompt_def['name']}")
        print(f"  Prompt: {prompt_def['prompt'][:80]}...")

        start = time.perf_counter()
        inputs = tokenizer(prompt_def["prompt"], return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=prompt_def["max_tokens"],
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        gen_ms = (time.perf_counter() - start) * 1000

        if generated.startswith(prompt_def["prompt"]):
            generated = generated[len(prompt_def["prompt"]):].strip()

        tokens_gen = len(outputs[0]) - len(inputs["input_ids"][0])

        print(f"  Time: {gen_ms:.0f}ms | Tokens: {tokens_gen}")
        print(f"  Output:")
        for line in generated[:400].split("\n"):
            print(f"    {line}")
        if len(generated) > 400:
            print(f"    ... ({len(generated)} chars)")

        score_info = score_generation_quality(generated, prompt_def)
        all_scores.append({"id": prompt_def["id"], "name": prompt_def["name"], **score_info})

        bar = "#" * (score_info["pct"] // 10) + "." * (10 - score_info["pct"] // 10)
        print(f"  Score: {score_info['pct']:.0f}% [{score_info['grade']}] [{bar}]")
        print(f"  {score_info['details']}")

    # Scorecard
    print(f"\n{'=' * 78}")
    print(f"  LLM GENERATION - SCORECARD")
    print(f"{'=' * 78}")
    print(f"  {'ID':<5} {'Test':<35} {'Score':>6}  {'Grade':<12}")
    print(f"  {'-' * 5} {'-' * 35} {'-' * 6}  {'-' * 12}")
    for s in all_scores:
        print(f"  {s['id']:<5} {s['name'][:34]:<35} {s['pct']:>5.0f}%  {s['grade']:<12}")

    avg = sum(s["pct"] for s in all_scores) / len(all_scores) if all_scores else 0
    grade = "EXCELLENT" if avg >= 85 else "GOOD" if avg >= 70 else "FAIR" if avg >= 50 else "POOR"
    print(f"  {'-' * 5} {'-' * 35} {'-' * 6}  {'-' * 12}")
    print(f"  {'AVG':<5} {'OVERALL':<35} {avg:>5.0f}%  {grade:<12}")
    print(f"{'=' * 78}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="VaLLM Interactive Chat & LLM Generation Tests",
        epilog=(
            "Examples:\n"
            "  python -m app.tests.tests_interactive_chat                              # automated conversations\n"
            "  python -m app.tests.tests_interactive_chat --interactive                 # live chat\n"
            '  python -m app.tests.tests_interactive_chat --interactive "deploy EC2"    # chat with initial query\n'
            "  python -m app.tests.tests_interactive_chat --generate                    # direct LLM tests\n"
            "  python -m app.tests.tests_interactive_chat --url http://localhost:8746   # custom URL\n"
            "\n"
            "  pytest app/tests/tests_interactive_chat.py -v -s                        # pytest all conversations\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--interactive", nargs="?", const="", default=None,
                        metavar="QUERY",
                        help="Start live interactive chat (optionally with initial query)")
    parser.add_argument("--generate", action="store_true",
                        help="Run direct LLM generation tests (no server needed)")
    parser.add_argument("--url", default=BASE_URL,
                        help=f"Base URL (default: {BASE_URL})")
    args = parser.parse_args()

    if args.interactive is not None:
        interactive_chat(args.url, args.interactive)
    elif args.generate:
        run_generation_tests()
    else:
        run_automated_conversations(args.url)
