"""
VaLLM Usage Example - Test Cloud Recommendations Search

This script tests searching for recommendations from cloud_recommendations.csv

USAGE:
======
    # 1. Start the API server first (in another terminal):
    python -m app.app

    # 2. Run this example:
    python ./app/usage_example.py
"""

import json
import time
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 60
USE_V1_ONLY = True
TOP_K = 5
SHOW_CONTEXT = True
SHOW_REASONING_STEPS = True
SHOW_REQUEST_META = True
CONTEXT_PREVIEW_CHARS = 220

# =============================================================================
# QUESTIONS TO TEST
# =============================================================================
# Keep questions aligned to content in:
# - app/data/cloud_recommendations.csv
# - app/data/cloud_operations_provisionning_knowledge1.txt
QUESTIONS = [
    # Observability / tracing
    "opentelemetry traces show dropped spans at the edge ?",
    "why are traces missing after the ingress gateway and how to fix sampling?",
    "jaeger shows gaps between services in a trace, what should i check?",
    # Cloud operations / incidents
    "kubernetes node became unreachable and workloads are crashing, what is the remediation?",
    "pods stuck in CrashLoopBackOff after a deployment, how do i troubleshoot?",
    "high cpu on control plane nodes causing api timeouts, what steps should we take?",
    # Security / reliability recommendations
    "web app leaking internal stack traces on 500 errors, how do i fix it?",
    "how to stop public s3 bucket access and enforce least privilege?",
    "database connection pool exhausted during traffic spikes, how to mitigate?",
    # Networking / edge
    "edge load balancer returns 502 intermittently, what checks should i perform?",
    "clients see tls handshake failures after cert rotation, how to recover?",
    # New provisioning questions
    "python boto3 to provision HA ec2 instance with load balance an autocall",
    "provision production gade eks with 3 nodes",
]


def _raise_for_status(response: requests.Response) -> None:
    """Raise with useful server response details."""
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = response.text.strip()
        msg = f"{exc}"
        if body:
            msg = f"{msg}\nServer response:\n{body}"
        raise requests.HTTPError(msg) from exc


def _post_json(url: str, payload: dict) -> dict:
    start = time.perf_counter()
    response = requests.post(url, json=payload, timeout=TIMEOUT)
    duration_ms = (time.perf_counter() - start) * 1000
    _raise_for_status(response)
    data = response.json()
    data["_meta"] = {
        "status_code": response.status_code,
        "duration_ms": round(duration_ms, 2),
        "request_id": response.headers.get("X-Request-ID"),
        "url": url,
        "payload": payload,
    }
    return data


def query_v1(query_text: str, top_k: int = 5) -> dict:
    """Full RAG query with reasoning engine (V1)."""
    url = f"{BASE_URL}/api/model/v1/query"
    payload = {"query": query_text, "top_k": top_k, "include_reasoning": True}
    return _post_json(url, payload)


def query_v2(query_text: str, top_k: int = 5) -> dict:
    """NLP-enhanced query with entity extraction (V2)."""
    url = f"{BASE_URL}/api/model/v2/query"
    payload = {"query": query_text, "top_k": top_k, "extract_entities": True, "include_recommendations": True}
    return _post_json(url, payload)


def _print_context(context_items: list) -> None:
    if not context_items:
        print("   (no context returned)")
        return
    for idx, item in enumerate(context_items, 1):
        doc = (item.get("document") or "").strip().replace("\n", " ")
        preview = doc[:CONTEXT_PREVIEW_CHARS]
        if len(doc) > CONTEXT_PREVIEW_CHARS:
            preview = f"{preview}..."
        doc_type = item.get("type", "unknown")
        score = item.get("score", 0.0)
        print(f"   {idx}. [{doc_type}] score={score:.4f} | {preview}")


def health_check() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def main():
    print("\n" + "=" * 70)
    print("🧪 VaLLM - Testing Cloud Recommendations Search")
    print("=" * 70)
    
    # Check if API is running
    if not health_check():
        print("\n❌ ERROR: API is not running!")
        print("   Please start it first with: python -m app.app")
        return
    
    print("\n✅ API is online!")
    print(f"\n📝 Questions: {len(QUESTIONS)}")
    print("=" * 70)

    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n\n📝 Question {i}/{len(QUESTIONS)}: {question}")
        print("-" * 70)

        # ======================================================================
        # TEST 1: V1 Query with Reasoning
        # ======================================================================
        print("\n🧠 TEST 1: RAG Query with Reasoning (/api/model/v1/query)")
        print("-" * 50)

        try:
            result = query_v1(question, top_k=TOP_K)
            meta = result.get("_meta", {})

            print(f"\n📝 Response:")
            print(f"   {result.get('response', 'No response')[:500]}")

            if result.get('reasoning'):
                print(f"\n🎯 Intent: {result['reasoning'].get('intent', 'unknown')}")
                print(f"📊 Confidence: {result['reasoning'].get('confidence', 0):.0%}")
                if SHOW_REASONING_STEPS:
                    steps = result['reasoning'].get('steps') or []
                    if steps:
                        print("\n🧭 Reasoning Steps:")
                        for s_idx, step in enumerate(steps, 1):
                            print(f"   {s_idx}. {step}")

            print(f"\n📚 Retrieved {len(result.get('context', []))} context documents")
            if SHOW_CONTEXT:
                print("\n🔎 Context Preview:")
                _print_context(result.get("context", []))

            if SHOW_REQUEST_META:
                print("\n🧾 Request Meta:")
                print(f"   status_code={meta.get('status_code')} duration_ms={meta.get('duration_ms')}")
                print(f"   request_id={meta.get('request_id')}")
                payload = meta.get("payload") or {}
                print(f"   payload={json.dumps(payload, ensure_ascii=True)}")

        except Exception as e:
            print(f"❌ Error: {e}")

        if not USE_V1_ONLY:
            # ==================================================================
            # TEST 2: V2 Query with NLP Entity Extraction
            # ==================================================================
            print("\n🔬 TEST 2: NLP Query with Entity Extraction (/api/model/v2/query)")
            print("-" * 50)

            try:
                result = query_v2(question, top_k=TOP_K)
                meta = result.get("_meta", {})

                print(f"\n📝 Response:")
                response = result.get('response', 'No response')
                # Print response with proper formatting
                for line in response.split('\n'):
                    print(f"   {line}")

                # Show extracted entities
                entities = result.get('entities', [])
                if entities:
                    print(f"\n🏷️  Extracted Entities ({len(entities)}):")
                    for e in entities[:8]:
                        print(f"    • {e.get('text')} [{e.get('category')}]")

                # Show AI recommendations
                recommendations = result.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 AI-Generated Recommendations:")
                    for j, rec in enumerate(recommendations, 1):
                        print(f"    {j}. {rec}")

                # Show NLP info
                nlp_info = result.get('nlp_info', {})
                print(f"\n🔧 NLP Status: spaCy={'✅' if nlp_info.get('spacy_available') else '❌'}")

                if SHOW_REQUEST_META:
                    print("\n🧾 Request Meta:")
                    print(f"   status_code={meta.get('status_code')} duration_ms={meta.get('duration_ms')}")
                    print(f"   request_id={meta.get('request_id')}")
                    payload = meta.get("payload") or {}
                    print(f"   payload={json.dumps(payload, ensure_ascii=True)}")

            except Exception as e:
                print(f"❌ Error: {e}")
    
    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print("""
Expected Result for INC-CUST-0006 (sample):
──────────────────────────────────────────
• Incident ID: INC-CUST-0006
• Timestamp: 2024-01-15 18:03:00
• Severity: high
• Service: helm
• Region: ap-southeast-1
• Title: Container CrashLoopBackOff
• Description: Node became unreachable impacting workloads
• Status: investigating
""")


if __name__ == "__main__":
    main()
