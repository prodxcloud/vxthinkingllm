
import unittest
import asyncio
import sys
import logging
import os
import requests
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Setup path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Import app components (using try block to avoid ImportErrors during discovery)
try:
    from app.app import health
    from app.reasoning import ReasoningEngine
    from app.embeddings import VectorStore
    from app.routes import (
        QueryRequest,
        TerminalRequest,
        DeveloperRequest,
        V3QueryRequest,
        query_endpoint,
        terminal_endpoint,
        developer_endpoint,
        v3_query_endpoint,
    )
except ImportError as e:
    raise ImportError(
        "Failed to import app modules for tests. Run from repo root with "
        "`python -m app.tests` or ensure the app package is importable."
    ) from e

# Configure logging globally
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class DummyRequest:
    def __init__(self, vector_store, reasoning_engine):
        self.app = SimpleNamespace(
            state=SimpleNamespace(
                vector_store=vector_store,
                reasoning_engine=reasoning_engine,
            )
        )
        # Add state attribute for request_id (used by route handlers)
        self.state = SimpleNamespace(request_id="test-request-id")


class TestCloudOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Global Setup"""
        # Create a mock vector store and reasoning engine
        cls.mock_vector_store = MagicMock(spec=VectorStore)
        cls.mock_reasoning_engine = MagicMock(spec=ReasoningEngine)
        
        # Configure the mock reasoning engine's reason method
        cls.mock_reasoning_engine.reason = AsyncMock(return_value={
            'intent': 'provision_vm',
            'steps': [
                {'type': 'analyze', 'content': 'Detected provision intent', 'confidence': 0.9, 'metadata': {}},
                {'type': 'search', 'content': 'Found templates', 'confidence': 0.8, 'metadata': {}}
            ],
            'final_answer': "To provision the VM, use the t2.micro instance type with Ubuntu 22.04.",
            'confidence': 0.95,
            'context_used': "doc1 | doc2"
        })
        
        # Configure query search results
        cls.mock_vector_store.search = AsyncMock(return_value=[
             {
                'document': 'config: t2.micro, ami: ubuntu-22.04', 
                'metadata': {'type': 'configuration', 'raw_data': {'title': 'Web Server'}}, 
                'score': 0.88
            },
            {
                'document': 'incident: VM creation failed due to quota', 
                'metadata': {'type': 'incident', 'raw_data': {'title': 'Quota Exceeded', 'severity': 'high'}}, 
                'score': 0.75
            }
        ])

        cls.request = DummyRequest(
            vector_store=cls.mock_vector_store,
            reasoning_engine=cls.mock_reasoning_engine,
        )

    def test_01_health_check(self):
        """Test API availability"""
        logger.info("\n🧪 [Test 01] Checking API Health Endpoint...")
        result = run_async(health())
        logger.info(f"   Response Body: {result}")
        logger.info("   LLM Input: N/A (health check)")
        logger.info(f"   LLM Output: {result}")
        self.assertEqual(result, {"status": "healthy"})
        logger.info("   ✅ Health check passed")

    def test_02_query_provision_vm(self):
        """Test querying for VM provisioning"""
        logger.info("\n🧪 [Test 02] Testing Query Endpoint (Provisioning Intent)...")
        payload = QueryRequest(
            query=(
                "Design a high-availability production environment with SOC2 compliance, "
                "Multi-AZ EKS, and WAF/Shield. What is the recommended baseline policy?"
            ),
            include_reasoning=True,
        )
        logger.info(f"   Payload: {payload.model_dump()}")
        logger.info(f"   LLM Input: {payload.query}")
        
        # Override specific mock behavior for this test if needed
        self.mock_reasoning_engine.reason.return_value = {
             'intent': 'provision',
             'steps': [{'type': 'plan', 'content': 'Planning VM', 'confidence': 1.0, 'metadata': {}}],
             'final_answer': "You should use Terraform module x.",
             'confidence': 0.9
        }
        
        data = run_async(query_endpoint(payload, self.request))
        logger.info(f"   LLM Output: {data.get('response')}")
        
        self.assertIn("response", data)
        self.assertIn("reasoning", data)
        self.assertIn("context", data)
        self.assertEqual(data['reasoning']['intent'], 'provision')
        self.assertEqual(len(data['context']), 2) # matches the mock setup
        
        logger.info(f"   Detected Intent: {data['reasoning']['intent']}")
        logger.info(f"   Reasoning Steps: {len(data['reasoning']['steps'])}")
        logger.info(f"   Context Documents: {len(data['context'])}")
        logger.info("   ✅ Provisioning query test passed")

    def test_03_query_troubleshoot_incident(self):
        """Test querying for incident troubleshooting"""
        logger.info("\n🧪 [Test 03] Testing Query Endpoint (Troubleshooting + Filter)...")
        payload = QueryRequest(
            query=(
                "We need a HIPAA workload with PHI data handling. Confirm the required "
                "network placement, encryption, and access logging rules."
            ),
            filter_type="incident",
        )
        logger.info(f"   Payload: {payload.model_dump()}")
        logger.info(f"   LLM Input: {payload.query}")
        
        self.mock_reasoning_engine.reason.return_value = {
             'intent': 'troubleshoot',
             'steps': [],
             'final_answer': "Check security groups and network ACLs.",
             'confidence': 0.85
        }
        
        data = run_async(query_endpoint(payload, self.request))
        logger.info(f"   LLM Output: {data.get('response')}")
        
        self.assertEqual(data['response'], "Check security groups and network ACLs.")
        logger.info(f"   Response: {data['response']}")
        
        # Verify vector store was searched with filter
        self.mock_vector_store.search.assert_awaited_with(
            query=(
                "We need a HIPAA workload with PHI data handling. Confirm the required "
                "network placement, encryption, and access logging rules."
            ),
            top_k=5,
            filter_type="incident"
        )
        logger.info("   ✅ Filter type applied correctly to vector search")
        logger.info("   ✅ Troubleshooting test passed")

    def test_04_terminal_command_analysis(self):
        """Test terminal command explanation"""
        logger.info("\n🧪 [Test 04] Testing Terminal Endpoint...")
        payload = TerminalRequest(
            command="aws s3api put-bucket-lifecycle-configuration --bucket data-pipeline --lifecycle-configuration file://lifecycle.json",
            include_explanation=True,
        )
        logger.info(f"   Command: {payload.command}")
        logger.info(f"   LLM Input: {payload.command}")
        
        self.mock_reasoning_engine.reason.return_value = {
             'intent': 'analyze',
             'steps': [],
             'final_answer': "This command lists all pods in all namespaces.",
             'confidence': 0.99
        }
        
        data = run_async(terminal_endpoint(payload, self.request))
        logger.info(f"   LLM Output: {data.get('response')}")
        
        self.assertIn("This command lists all pods", data['response'])
        self.assertIn("incidents", data)
        self.assertIn("recommendations", data)
        
        logger.info(f"   Analysis: {data['response']}")
        logger.info(f"   Incidents Found: {len(data['incidents'])}")
        logger.info(f"   Recommendations: {len(data['recommendations'])}")
        logger.info("   ✅ Terminal analysis test passed")

    def test_05_developer_code_gen(self):
        """Test developer code assistance"""
        logger.info("\n🧪 [Test 05] Testing Developer Endpoint (Code Gen)...")
        payload = DeveloperRequest(
            query=(
                "Generate Terraform for a production VPC with Flow Logs enabled, "
                "private DNS namespace, and KMS-backed encryption defaults."
            ),
            include_code=True,
        )
        logger.info(f"   Query: {payload.query}")
        logger.info(f"   LLM Input: {payload.query}")
        
        self.mock_reasoning_engine.reason.return_value = {
             'intent': 'provision',
             'steps': [],
             'final_answer': "Here is the terraform code for S3.",
             'confidence': 0.95
        }
        
        data = run_async(developer_endpoint(payload, self.request))
        logger.info(f"   LLM Output: {data.get('response')}")
        
        self.assertIn("code_examples", data)
        self.assertEqual(data['model'], "vallm-developer-v1")
        
        logger.info("   ✅ Code examples returned")
        logger.info(f"   Model used: {data['model']}")
        logger.info("   ✅ Developer endpoint test passed")

    def test_06_v3_unusual_incident_patterns(self):
        """Test V3 incident pattern endpoint"""
        logger.info("\n🧪 [Test 06] Testing V3 Incident Patterns Endpoint...")
        payload = V3QueryRequest(
            query=(
                "Unusual incident patterns tied to VPN flaps, private subnet misconfigurations, "
                "and multi-AZ failover issues in cloud environments."
            ),
            top_k=5,
            include_reasoning=True,
            focus="cloud_devops",
        )
        logger.info(f"   LLM Input: {payload.query}")

        self.mock_vector_store.search.return_value = [
            {
                "document": "incident: VPN tunnel drops on AWS",
                "metadata": {
                    "raw": {
                        "incident_id": "INC-100",
                        "severity": "critical",
                        "category": "networking",
                        "service": "aws",
                        "error_code": "VPN_DISCONNECT",
                        "tags": "aws+vpn+network",
                        "timestamp": "2026-01-17T08:15:00Z",
                    }
                },
                "score": 0.91,
            },
            {
                "document": "incident: CI pipeline timeout",
                "metadata": {
                    "raw": {
                        "incident_id": "INC-101",
                        "severity": "high",
                        "category": "cicd",
                        "service": "github-actions",
                        "error_code": "RUNNER_TIMEOUT",
                        "tags": "cicd+devops",
                        "timestamp": "2026-01-17T11:00:00Z",
                    }
                },
                "score": 0.83,
            },
        ]

        self.mock_reasoning_engine.reason.return_value = {
            "intent": "analyze_incidents",
            "steps": [],
            "final_answer": "Detected unusual high-severity networking and CI/CD incidents.",
            "confidence": 0.92,
        }

        data = run_async(v3_query_endpoint(payload, self.request))
        logger.info(f"   LLM Output: {data.get('response')}")

        self.assertEqual(data["model"], "vallm-v3-enhanced")
        self.assertIn("metrics", data)
        self.assertIn("success_metrics", data)
        self.assertIn("unusual_incidents", data)
        self.assertGreaterEqual(data["metrics"]["unusual_count"], 1)
        self.assertEqual(data["focus"], "cloud_devops")
        self.assertIn("signals_used", data)
        self.assertIn("sklearn", data["signals_used"])
        self.assertIn("xgboost", data["signals_used"])
        self.assertIn("pytorch", data["signals_used"])


@unittest.skipUnless(
    os.getenv("VALLM_LIVE_TESTS", "").lower() in {"1", "true", "yes"},
    "Set VALLM_LIVE_TESTS=true to run live API smoke tests."
)
class LiveSmokeTests(unittest.TestCase):
    BASE_URL = os.getenv("VALLM_BASE_URL", "http://127.0.0.1:8000")
    TIMEOUT = 30

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.BASE_URL}{path}"
        response = requests.post(url, json=payload, timeout=self.TIMEOUT)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            body = response.text.strip()
            detail = f"{exc}"
            if body:
                detail = f"{detail}\nServer response:\n{body}"
            raise requests.HTTPError(detail) from exc
        return response.json()

    def test_live_health(self):
        response = requests.get(f"{self.BASE_URL}/health", timeout=5)
        self.assertEqual(response.status_code, 200)

    def test_live_v1_dr_site(self):
        payload = {
            "query": (
                "Design a disaster recovery site with RPO < 15 minutes and RTO < 1 hour. "
                "Include replication and failover controls."
            ),
            "top_k": 3,
            "include_reasoning": True,
        }
        data = self._post("/api/model/v1/query", payload)
        self.assertIn("response", data)

    def test_live_v1_private_subnet(self):
        payload = {
            "query": (
                "Deploy an internal payroll API with PII. Should it be in private subnet, "
                "and what ingress controls are required?"
            ),
            "top_k": 3,
            "include_reasoning": True,
        }
        data = self._post("/api/model/v1/query", payload)
        self.assertIn("response", data)

    def test_live_v1_openvpn(self):
        payload = {
            "query": (
                "Provision OpenVPN in a private subnet with UDP/1194 exposure, MFA, "
                "and restricted VPC peering to 10.50.0.0/16."
            ),
            "top_k": 3,
            "include_reasoning": True,
        }
        data = self._post("/api/model/v1/query", payload)
        self.assertIn("response", data)

if __name__ == '__main__':
    unittest.main()
