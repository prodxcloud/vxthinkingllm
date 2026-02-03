"""
Interactive User Tests for VaLLM
Command-line interface for testing VaLLM with user input
Usage: python -m app.tests.user_tests
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from typing import Optional


class VaLLMClient:
    """Simple client for testing VaLLM API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> bool:
        """Check if service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def query_v1(self, query: str, include_reasoning: bool = True, top_k: int = 5) -> Optional[dict]:
        """Query V1 endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/api/model/v1/query",
                json={
                    "query": query,
                    "include_reasoning": include_reasoning,
                    "top_k": top_k
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Query failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"   Response: {e.response.text}")
                except:
                    pass
            return None
    
    def search(self, query: str, top_k: int = 5) -> Optional[dict]:
        """Search endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json={"query": query, "top_k": top_k},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return None
    
    def get_metrics(self) -> Optional[str]:
        """Get Prometheus metrics"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"⚠️  Metrics not available: {e}")
            return None
    
    def get_health_detailed(self) -> Optional[dict]:
        """Get detailed health check"""
        try:
            response = requests.get(f"{self.base_url}/health/ready", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Detailed health not available: {e}")
            return None


def print_response(response: dict, query: str):
    """Pretty print response"""
    print("\n" + "="*70)
    print(f"Query: {query}")
    print("="*70)
    
    if "response" in response:
        print(f"\n📝 Response:")
        print(f"   {response['response']}")
    
    if "reasoning" in response:
        reasoning = response['reasoning']
        print(f"\n🧠 Reasoning:")
        print(f"   Intent: {reasoning.get('intent', 'unknown')}")
        print(f"   Confidence: {reasoning.get('confidence', 0):.2f}")
        if "steps" in reasoning:
            print(f"   Steps: {len(reasoning['steps'])}")
            for i, step in enumerate(reasoning['steps'][:3], 1):
                print(f"      {i}. {step.get('type', 'unknown')}: {step.get('content', '')[:60]}...")
    
    if "context" in response:
        print(f"\n📚 Context ({len(response['context'])} documents):")
        for i, ctx in enumerate(response['context'][:3], 1):
            doc_type = ctx.get('type', 'unknown')
            score = ctx.get('score', 0)
            doc = ctx.get('document', '')[:80]
            print(f"   {i}. [{doc_type}] (score: {score:.2f}): {doc}...")
    
    print("="*70 + "\n")


def interactive_mode():
    """Interactive command-line testing"""
    print("\n" + "="*70)
    print("VaLLM Interactive Test Client")
    print("="*70)
    print("\nCommands:")
    print("  <query>           - Query VaLLM V1 endpoint")
    print("  search <query>    - Search vector store")
    print("  health            - Check service health")
    print("  metrics           - View Prometheus metrics")
    print("  health-detailed   - Detailed health check")
    print("  help              - Show this help")
    print("  quit/exit         - Exit")
    print("\n" + "="*70 + "\n")
    
    base_url = input("Enter VaLLM base URL (default: http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    client = VaLLMClient(base_url)
    
    # Check health first
    print("\n🔍 Checking service health...")
    if not client.health_check():
        print("❌ Service is not available. Please start VaLLM first.")
        print("   Run: python -m app.app")
        return
    print("✅ Service is healthy!\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("VaLLM> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\nCommands:")
                print("  <query>           - Query VaLLM V1 endpoint")
                print("  search <query>    - Search vector store")
                print("  health            - Check service health")
                print("  metrics           - View Prometheus metrics")
                print("  health-detailed   - Detailed health check")
                print("  help              - Show this help")
                print("  quit/exit         - Exit\n")
                continue
            
            if user_input.lower() == 'health':
                if client.health_check():
                    print("✅ Service is healthy")
                else:
                    print("❌ Service is unhealthy")
                continue
            
            if user_input.lower() == 'health-detailed':
                health = client.get_health_detailed()
                if health:
                    print("\n📊 Detailed Health:")
                    import json
                    print(json.dumps(health, indent=2))
                continue
            
            if user_input.lower() == 'metrics':
                metrics = client.get_metrics()
                if metrics:
                    print("\n📈 Prometheus Metrics:")
                    print(metrics[:500] + "..." if len(metrics) > 500 else metrics)
                continue
            
            if user_input.lower().startswith('search '):
                query = user_input[7:].strip()
                if not query:
                    print("❌ Please provide a search query")
                    continue
                
                print(f"\n🔍 Searching for: {query}")
                result = client.search(query)
                if result and "results" in result:
                    print(f"\n📚 Found {len(result['results'])} results:")
                    for i, r in enumerate(result['results'][:5], 1):
                        score = r.get('score', 0)
                        text = r.get('text', '')[:100]
                        print(f"   {i}. (score: {score:.2f}): {text}...")
                continue
            
            # Default: treat as V1 query
            print(f"\n🤔 Processing query: {user_input}")
            response = client.query_v1(user_input)
            
            if response:
                print_response(response, user_input)
            else:
                print("❌ Failed to get response")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    interactive_mode()
