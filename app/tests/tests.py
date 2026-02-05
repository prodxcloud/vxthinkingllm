"""
Interactive and batch tests for VaLLM (LLM model only).
- Default: run 5 questions against the app on port 8002 (V1 query = LLM + reasoning).
- Optional: python -m app.tests.tests --interactive  for interactive mode.

Start the app first (e.g. uvicorn app.app:app --host 0.0.0.0 --port 8002).
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from typing import Optional

# App runs on port 8002
BASE_URL = "http://localhost:8002"

# 5 prompts as the user would say in the assistant (cloud deployment commands, not "how")
LLM_QUESTIONS = [
    "Deploy a small EC2 instance with 30GB disk.",
    "I want to deploy a t2.micro in us-east-1 with Ubuntu.",
    "Deploy a PostgreSQL database on my VM.",
    "Show me recent incidents or outages in the environment.",
    "Give me cost optimization recommendations for AWS.",
]


class VaLLMClient:
    """Client for VaLLM API (LLM / V1 query only in this test file)."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def query_v1(self, query: str, include_reasoning: bool = True, top_k: int = 5) -> Optional[dict]:
        """Query V1 endpoint (LLM + reasoning)."""
        try:
            response = requests.post(
                f"{self.base_url}/api/model/v1/query",
                json={
                    "query": query,
                    "include_reasoning": include_reasoning,
                    "top_k": top_k,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Query failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    print(f"   Response: {e.response.text[:500]}")
                except Exception:
                    pass
            return None


def print_response(response: dict, query: str) -> None:
    """Pretty print a V1 query response."""
    print("\n" + "=" * 70)
    print(f"Query: {query}")
    print("=" * 70)

    if "response" in response:
        print("\nResponse:")
        print(response["response"])

    if "reasoning" in response:
        r = response["reasoning"]
        print("\nReasoning:")
        print(f"  Intent: {r.get('intent', 'unknown')}")
        print(f"  Confidence: {r.get('confidence', 0):.2f}")
        if r.get("steps"):
            print(f"  Steps: {len(r['steps'])}")
            for i, step in enumerate(r["steps"][:3], 1):
                content = step.get("content", "")[:80]
                print(f"    {i}. {content}...")

    if "context" in response and response["context"]:
        print(f"\nContext ({len(response['context'])} docs):")
        for i, ctx in enumerate(response["context"][:2], 1):
            doc = (ctx.get("document") or "")[:80]
            print(f"  {i}. {doc}...")

    print("=" * 70 + "\n")


def run_five_questions(base_url: str = BASE_URL) -> None:
    """Run 5 questions against the LLM (V1 query) on the app at base_url."""
    print("\n" + "=" * 70)
    print("VaLLM – 5 questions (LLM model only, port 8002)")
    print("=" * 70)
    print(f"Base URL: {base_url}")
    print("Endpoint: POST /api/model/v1/query")
    print("=" * 70 + "\n")

    client = VaLLMClient(base_url)

    print("Checking service health...")
    if not client.health_check():
        print("Service not available. Start the app first:")
        print("  uvicorn app.app:app --host 0.0.0.0 --port 8002")
        print("  (or: python -m app.app  if it listens on 8002)")
        return
    print("OK\n")

    for i, query in enumerate(LLM_QUESTIONS, 1):
        print(f"[{i}/5] Sending: {query[:60]}...")
        response = client.query_v1(query)
        if response:
            print_response(response, query)
        else:
            print(f"  Failed to get response for question {i}\n")


def interactive_mode(base_url: str = BASE_URL) -> None:
    """Interactive command-line testing (LLM V1 query only)."""
    print("\n" + "=" * 70)
    print("VaLLM Interactive Test (LLM model only)")
    print("=" * 70)
    print("Commands:")
    print("  <query>     – Query V1 (LLM + reasoning)")
    print("  health      – Health check")
    print("  help        – Show help")
    print("  quit/exit   – Exit")
    print("=" * 70 + "\n")

    client = VaLLMClient(base_url)
    if not client.health_check():
        print("Service not available. Start the app on port 8002 first.")
        return
    print("Service OK.\n")

    while True:
        try:
            user_input = input("VaLLM> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Bye.")
                break
            if user_input.lower() == "help":
                print("  <query>   – Query V1  |  health  |  quit")
                continue
            if user_input.lower() == "health":
                print("OK" if client.health_check() else "Unhealthy")
                continue

            response = client.query_v1(user_input)
            if response:
                print_response(response, user_input)
            else:
                print("Request failed.")
        except KeyboardInterrupt:
            print("\nBye.")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VaLLM tests (LLM only, app on port 8002)")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive mode instead of 5 questions",
    )
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Base URL (default: {BASE_URL})",
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_mode(args.url)
    else:
        run_five_questions(args.url)
