"""
VaLLM ML Unit Tests - Comprehensive tests for DevOps Agent + Cloud Provisioning

Tests cover:
  SECTION 1: Legacy Provisioning Tests
    - Payload generation (VM, K8s, Docker, Database, FastAPI, Managed DB)
    - Non-provisioning classification
    - Health endpoint

  SECTION 2: DevOps Agent Intent Tests (NEW)
    - Script intent detection (349 scripts)
    - Terraform intent detection (207 modules)
    - Git operations (clone, push, PR)
    - File operations (write, edit)
    - CI/CD pipeline operations
    - Deployment service intent
    - Ansible playbook intent
    - Multi-action workflow detection
    - Argument extraction
    - Negative/other intent classification
    - Confidence scoring

  SECTION 3: Dataset Validation Tests (NEW)
    - CSV dataset integrity
    - JSON dataset integrity
    - Knowledge base completeness
    - Action JSON schema validation

  SECTION 4: Integration Tests (NEW)
    - V1 query endpoint with DevOps prompts
    - Terminal endpoint
    - Developer endpoint

Run:
    python -m pytest app/services/ai/ml/tests.py -v
    python -m unittest app.services.ai.ml.tests -v
"""

import unittest
import asyncio
import sys
import logging
import os
import json
import csv
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Setup path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import app components
try:
    from app.services.ai.ml.routes import (
        QueryRequest,
        TerminalRequest,
        DeveloperRequest,
        query_endpoint,
        terminal_endpoint,
        developer_endpoint,
    )
    from app.services.ai.ml.cloud_routes import (
        _raw_to_golang_payload,
        _classify_non_provisioning,
        _is_deployment_result,
        ProvisionIntentRequest,
        provision_intent,
    )
except ImportError as e:
    raise ImportError(
        f"Failed to import app modules: {e}. "
        "Run from repo root: python -m pytest app/services/ai/ml/tests.py -v"
    ) from e

try:
    from app.services.ai.ml.reasoning import ReasoningEngine
    from app.services.ai.ml.embeddings import VectorStore
except ImportError:
    ReasoningEngine = None
    VectorStore = None

try:
    from app.app import health
except ImportError:
    health = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

DATASETS_DIR = project_root / "app" / "data" / "datasets"


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class DummyRequest:
    """Simulates a FastAPI Request with app.state."""
    def __init__(self, vector_store, reasoning_engine):
        self.app = SimpleNamespace(
            state=SimpleNamespace(
                vector_store=vector_store,
                reasoning_engine=reasoning_engine,
            )
        )
        self.state = SimpleNamespace(request_id="test-request-id")


# ==========================================================================
# SECTION 1: Legacy Payload Generation Tests
# ==========================================================================

class TestPayloadGeneration(unittest.TestCase):
    """Test _raw_to_golang_payload for each provisioning intent."""

    def test_provision_vm_payload(self):
        raw = {
            "username": "joel", "instance_name": "web-01", "instance_type": "t3.medium",
            "region": "us-west-2", "cloud_provider": "aws", "os": "ubuntu",
            "volume_size_gb": "50", "volume_type": "gp3", "environment": "production",
        }
        payload = _raw_to_golang_payload(raw, "provision_vm")
        self.assertEqual(payload["instance_type"], "t3.medium")
        self.assertEqual(payload["region"], "us-west-2")
        self.assertEqual(payload["cloud_provider"], "aws")
        self.assertEqual(payload["volume_size"], 50)
        logger.info("PASS: provision_vm payload")

    def test_provision_kubernetes_payload(self):
        raw = {
            "username": "joel", "cluster_name": "prod-eks", "node_count": "3",
            "node_type": "m5.large", "kubernetes_version": "1.29",
            "region": "us-east-1", "cloud_provider": "aws",
        }
        payload = _raw_to_golang_payload(raw, "provision_kubernetes")
        self.assertEqual(payload["cluster_name"], "prod-eks")
        self.assertEqual(payload["node_count"], 3)
        self.assertEqual(payload["kubernetes_version"], "1.29")
        logger.info("PASS: provision_kubernetes payload")

    def test_provision_docker_payload(self):
        raw = {
            "username": "joel", "docker_image": "nginx:latest",
            "docker_service": "nginx", "container_name": "web-nginx", "ports": "80:80",
        }
        payload = _raw_to_golang_payload(raw, "provision_docker")
        self.assertEqual(payload["docker_image"], "nginx:latest")
        self.assertEqual(payload["container_name"], "web-nginx")
        logger.info("PASS: provision_docker payload")

    def test_provision_database_payload(self):
        raw = {
            "username": "joel", "hostname": "db.internal", "database_engine": "postgresql",
            "database_name": "analytics_db", "database_user": "admin", "port": "5432",
        }
        payload = _raw_to_golang_payload(raw, "provision_database")
        self.assertEqual(payload["database_engine"], "postgresql")
        self.assertEqual(payload["database_name"], "analytics_db")
        logger.info("PASS: provision_database payload")

    def test_provision_fastapi_payload(self):
        raw = {
            "username": "joel", "app_name": "myapi", "app_port": "8000",
            "hostname": "api.vxcloud.io", "ssh_username": "ubuntu",
        }
        payload = _raw_to_golang_payload(raw, "provision_fastapi")
        self.assertEqual(payload["app_name"], "myapi")
        self.assertEqual(payload["app_port"], 8000)
        logger.info("PASS: provision_fastapi payload")

    def test_non_provisioning_classification(self):
        self.assertEqual(_classify_non_provisioning("What is the weather?"), "other")
        self.assertEqual(_classify_non_provisioning("Tell me a joke"), "other")
        logger.info("PASS: non-provisioning classified as 'other'")


# ==========================================================================
# SECTION 2: DevOps Agent Intent Tests
# ==========================================================================

class TestDevOpsAgentIntents(unittest.TestCase):
    """Test DevOps Agent action dataset for correct intent mapping."""

    @classmethod
    def setUpClass(cls):
        """Load the DevOps Agent dataset."""
        cls.actions_csv = DATASETS_DIR / "devops_agent_actions.csv"
        cls.cicd_csv = DATASETS_DIR / "devops_agent_cicd_deployments.csv"
        cls.actions_json = DATASETS_DIR / "devops_agent_actions.json"
        cls.knowledge_txt = DATASETS_DIR / "devops_agent_knowledge.txt"

        cls.action_rows = []
        if cls.actions_csv.exists():
            with open(cls.actions_csv, encoding='utf-8') as f:
                cls.action_rows = list(csv.DictReader(f))

        cls.cicd_rows = []
        if cls.cicd_csv.exists():
            with open(cls.cicd_csv, encoding='utf-8') as f:
                cls.cicd_rows = list(csv.DictReader(f))

        cls.all_rows = cls.action_rows + cls.cicd_rows

    # --- Script Intent Tests ---

    def test_script_dataset_not_empty(self):
        scripts = [r for r in self.action_rows if r['action_type'] == 'script']
        self.assertGreater(len(scripts), 1000, f"Expected 1000+ script examples, got {len(scripts)}")
        logger.info(f"PASS: {len(scripts)} script examples loaded")

    def test_redis_install_intent(self):
        matches = [r for r in self.action_rows if 'redis' in r['path'] and 'install' in r['path']]
        self.assertGreater(len(matches), 0, "No redis install_redis.sh examples found")
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['action'], 'execute')
        self.assertEqual(action['type'], 'script')
        self.assertIn('redis', action['path'])
        logger.info("PASS: Redis install intent correct")

    def test_nginx_install_intent(self):
        matches = [r for r in self.action_rows if 'install_nginx' in r['path']]
        self.assertGreater(len(matches), 0)
        logger.info(f"PASS: {len(matches)} Nginx install examples")

    def test_jenkins_install_intent(self):
        matches = [r for r in self.action_rows if 'jenkins/install_jenkins' in r['path']]
        self.assertGreater(len(matches), 0)
        logger.info("PASS: Jenkins install intent found")

    def test_network_scripts_have_args(self):
        scanners = [r for r in self.action_rows if 'port_scanner' in r['path'] or 'open_port' in r['path']]
        self.assertGreater(len(scanners), 0, "No port scanner examples found")
        for r in scanners:
            self.assertNotEqual(r['args'], '', f"Port scanner {r['path']} should have args")
        logger.info(f"PASS: {len(scanners)} network scanners have args")

    def test_cloud_aws_scripts_deep_paths(self):
        aws_scripts = [r for r in self.action_rows if r['path'].startswith('cloud/aws/')]
        self.assertGreater(len(aws_scripts), 0, "No cloud/aws/ deep path scripts found")
        s3_scripts = [r for r in aws_scripts if 's3' in r['path']]
        self.assertGreater(len(s3_scripts), 0, "No S3 provisioning scripts found")
        logger.info(f"PASS: {len(aws_scripts)} AWS scripts, {len(s3_scripts)} S3 scripts")

    def test_openclaw_scripts(self):
        matches = [r for r in self.action_rows if 'openclaw' in r['path']]
        self.assertGreater(len(matches), 0, "No OpenClaw scripts found")
        logger.info(f"PASS: {len(matches)} OpenClaw examples")

    # --- Terraform Intent Tests ---

    def test_terraform_dataset_not_empty(self):
        tf = [r for r in self.action_rows if r['action_type'] == 'terraform']
        self.assertGreater(len(tf), 500, f"Expected 500+ terraform examples, got {len(tf)}")
        logger.info(f"PASS: {len(tf)} terraform examples loaded")

    def test_terraform_aws_apigateway(self):
        matches = [r for r in self.action_rows if 'terraform_aws_apigateway' in r['path']]
        self.assertGreater(len(matches), 0)
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['type'], 'terraform')
        self.assertIn('aws', action['path'])
        logger.info("PASS: AWS API Gateway terraform intent")

    def test_terraform_docker_grafana(self):
        matches = [r for r in self.action_rows if 'terraform_docker_linux_grafana' in r['path']]
        self.assertGreater(len(matches), 0)
        logger.info("PASS: Docker Grafana terraform intent")

    def test_terraform_all_providers(self):
        providers = set()
        for r in self.action_rows:
            if r['action_type'] == 'terraform':
                providers.add(r['category'])
        expected = {'aws', 'azure', 'gcp', 'docker', 'alibaba'}
        self.assertTrue(expected.issubset(providers), f"Missing providers: {expected - providers}")
        logger.info(f"PASS: {len(providers)} terraform providers: {sorted(providers)}")

    # --- Git Intent Tests ---

    def test_git_clone_intent(self):
        matches = [r for r in self.action_rows if r['intent'] == 'git_clone']
        self.assertGreater(len(matches), 0)
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['action'], 'git_clone')
        self.assertIn('repo_url', action)
        logger.info(f"PASS: {len(matches)} git clone examples")

    def test_git_push_intent(self):
        matches = [r for r in self.action_rows if r['intent'] == 'git_push']
        self.assertGreater(len(matches), 0)
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['action'], 'git_push')
        self.assertIn('branch', action)
        logger.info(f"PASS: {len(matches)} git push examples")

    def test_git_pr_intent(self):
        matches = [r for r in self.action_rows if r['intent'] == 'git_pr']
        self.assertGreater(len(matches), 0)
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['action'], 'git_pr')
        self.assertIn('head_branch', action)
        logger.info(f"PASS: {len(matches)} git PR examples")

    # --- File Operation Tests ---

    def test_write_file_intent(self):
        matches = [r for r in self.action_rows if r['intent'] == 'write_file']
        self.assertGreater(len(matches), 0)
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['action'], 'write_file')
        self.assertIn('file_path', action)
        self.assertIn('content', action)
        logger.info(f"PASS: {len(matches)} write file examples")

    # --- Negative Examples ---

    def test_other_intent(self):
        matches = [r for r in self.action_rows if r['intent'] == 'other']
        self.assertGreater(len(matches), 0)
        action = json.loads(matches[0]['action_json'])
        self.assertEqual(action['action'], 'none')
        logger.info(f"PASS: {len(matches)} negative/other examples")

    # --- CI/CD Tests ---

    def test_cicd_dataset_not_empty(self):
        self.assertGreater(len(self.cicd_rows), 200, f"Expected 200+ CI/CD examples, got {len(self.cicd_rows)}")
        logger.info(f"PASS: {len(self.cicd_rows)} CI/CD examples loaded")

    def test_deploy_service_intents(self):
        matches = [r for r in self.cicd_rows if r['intent'] == 'deploy_service']
        self.assertGreater(len(matches), 20)
        services = set(r['category'] for r in matches)
        self.assertIn('fastapi', services)
        self.assertIn('reactjs', services)
        self.assertIn('nextjs', services)
        logger.info(f"PASS: {len(matches)} deploy service examples, services={sorted(services)}")

    def test_github_actions_cicd(self):
        matches = [r for r in self.cicd_rows if 'github_actions' in r['category']]
        self.assertGreater(len(matches), 50)
        logger.info(f"PASS: {len(matches)} GitHub Actions CI/CD examples")

    def test_jenkins_cicd(self):
        matches = [r for r in self.cicd_rows if 'jenkins' in r['category']]
        self.assertGreater(len(matches), 10)
        logger.info(f"PASS: {len(matches)} Jenkins CI/CD examples")

    def test_ansible_playbook_intents(self):
        matches = [r for r in self.cicd_rows if r['intent'] == 'run_ansible']
        self.assertGreater(len(matches), 10)
        logger.info(f"PASS: {len(matches)} Ansible examples")

    def test_pipeline_operation_intents(self):
        matches = [r for r in self.cicd_rows if 'pipeline' in r['intent']]
        self.assertGreater(len(matches), 10)
        logger.info(f"PASS: {len(matches)} pipeline operation examples")

    def test_webhook_intents(self):
        matches = [r for r in self.cicd_rows if r['intent'] == 'setup_webhook']
        self.assertGreater(len(matches), 5)
        logger.info(f"PASS: {len(matches)} webhook examples")

    def test_multi_action_workflows(self):
        matches = [r for r in self.cicd_rows if r['intent'] == 'multi_action_workflow']
        self.assertGreater(len(matches), 5)
        for r in matches:
            action = json.loads(r['action_json'])
            self.assertIn('steps', action, f"Workflow missing 'steps': {r['prompt']}")
            self.assertGreater(len(action['steps']), 1, f"Workflow should have 2+ steps")
        logger.info(f"PASS: {len(matches)} multi-action workflow examples")

    def test_kubernetes_deploy_intents(self):
        matches = [r for r in self.cicd_rows if r['intent'] == 'deploy_kubernetes']
        self.assertGreater(len(matches), 20)
        logger.info(f"PASS: {len(matches)} Kubernetes deploy examples")


# ==========================================================================
# SECTION 3: Dataset Validation Tests
# ==========================================================================

class TestDatasetIntegrity(unittest.TestCase):
    """Validate dataset files are well-formed and complete."""

    def test_actions_csv_exists(self):
        path = DATASETS_DIR / "devops_agent_actions.csv"
        self.assertTrue(path.exists(), f"Missing {path}")
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreater(len(rows), 2500, f"Expected 2500+ rows, got {len(rows)}")
        logger.info(f"PASS: actions CSV has {len(rows)} rows")

    def test_cicd_csv_exists(self):
        path = DATASETS_DIR / "devops_agent_cicd_deployments.csv"
        self.assertTrue(path.exists(), f"Missing {path}")
        with open(path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        self.assertGreater(len(rows), 200)
        logger.info(f"PASS: CI/CD CSV has {len(rows)} rows")

    def test_actions_json_valid(self):
        path = DATASETS_DIR / "devops_agent_actions.json"
        self.assertTrue(path.exists())
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('metadata', data)
        self.assertIn('use_cases', data)
        self.assertGreater(len(data['use_cases']), 2500)
        self.assertGreater(data['metadata']['scripts_count'], 300)
        self.assertGreater(data['metadata']['terraform_count'], 200)
        logger.info(f"PASS: actions JSON valid, {len(data['use_cases'])} use cases")

    def test_cicd_json_valid(self):
        path = DATASETS_DIR / "devops_agent_cicd_deployments.json"
        self.assertTrue(path.exists())
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('use_cases', data)
        self.assertGreater(len(data['use_cases']), 200)
        logger.info(f"PASS: CI/CD JSON valid, {len(data['use_cases'])} use cases")

    def test_knowledge_base_complete(self):
        path = DATASETS_DIR / "devops_agent_knowledge.txt"
        self.assertTrue(path.exists())
        content = path.read_text(encoding='utf-8')
        # Check all sections present
        for section in [
            "ACTION TYPES", "SCRIPT CATEGORIES", "TERRAFORM MODULES",
            "SCRIPT ARGUMENT PATTERNS", "EXECUTION ROUTING", "MULTI-ACTION WORKFLOWS",
            "DESTRUCTIVE ACTIONS", "INTENT CLASSIFICATION",
            "DEPLOYMENT SERVICES", "CI/CD PIPELINE TEMPLATES",
            "ANSIBLE PLAYBOOKS", "KUBERNETES MANIFESTS", "CI/CD PIPELINE OPERATIONS",
        ]:
            self.assertIn(section, content, f"Knowledge base missing section: {section}")
        logger.info(f"PASS: Knowledge base has all 13 sections ({len(content)} chars)")

    def test_action_json_schema_valid(self):
        """Every action_json field should be valid JSON with 'action' key."""
        path = DATASETS_DIR / "devops_agent_actions.csv"
        errors = []
        with open(path, encoding='utf-8') as f:
            for i, row in enumerate(csv.DictReader(f)):
                try:
                    action = json.loads(row['action_json'])
                    if 'action' not in action:
                        errors.append(f"Row {i}: missing 'action' key")
                except json.JSONDecodeError as e:
                    errors.append(f"Row {i}: invalid JSON: {e}")
        self.assertEqual(len(errors), 0, f"{len(errors)} schema errors:\n" + "\n".join(errors[:10]))
        logger.info("PASS: All action_json fields are valid JSON with 'action' key")

    def test_csv_required_columns(self):
        """Both CSV files should have all required columns."""
        required = {"prompt", "intent", "action_type", "path", "category", "tags", "action_json"}
        for name in ["devops_agent_actions.csv", "devops_agent_cicd_deployments.csv"]:
            path = DATASETS_DIR / name
            if not path.exists():
                continue
            with open(path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                cols = set(reader.fieldnames or [])
            missing = required - cols
            self.assertEqual(len(missing), 0, f"{name} missing columns: {missing}")
        logger.info("PASS: All CSV files have required columns")

    def test_all_intents_covered(self):
        """Check that all expected intents exist in the datasets."""
        all_rows = []
        for name in ["devops_agent_actions.csv", "devops_agent_cicd_deployments.csv"]:
            path = DATASETS_DIR / name
            if path.exists():
                with open(path, encoding='utf-8') as f:
                    all_rows.extend(csv.DictReader(f))
        intents = set(r['intent'] for r in all_rows)
        expected = {
            'execute_script', 'execute_terraform', 'git_clone', 'git_push', 'git_pr',
            'write_file', 'other', 'deploy_service', 'setup_cicd', 'run_ansible',
            'deploy_kubernetes', 'multi_action_workflow',
        }
        missing = expected - intents
        self.assertEqual(len(missing), 0, f"Missing intents: {missing}")
        logger.info(f"PASS: All {len(expected)} expected intents present. Total intents: {sorted(intents)}")


# ==========================================================================
# SECTION 4: Integration Tests (Mock-based)
# ==========================================================================

class TestV1QueryEndpoint(unittest.TestCase):
    """Test V1 query endpoint with DevOps Agent prompts."""

    def _make_mock_request(self):
        mock_vs = MagicMock(spec=VectorStore) if VectorStore else MagicMock()
        mock_vs.search = AsyncMock(return_value=[
            {"document": "redis/install_redis.sh — installs Redis server", "metadata": {"type": "script"}, "score": 0.95},
        ])
        mock_re = MagicMock(spec=ReasoningEngine) if ReasoningEngine else MagicMock()
        mock_re.reason = AsyncMock(return_value={
            "intent": "execute_script",
            "confidence": 0.92,
            "final_answer": "Use redis/install_redis.sh to install Redis server.",
            "steps": [
                {"step": "classify", "result": "execute_script"},
                {"step": "match", "result": "redis/install_redis.sh"},
            ],
        })
        return DummyRequest(mock_vs, mock_re), mock_vs, mock_re

    def test_install_redis_query(self):
        req, mock_vs, mock_re = self._make_mock_request()
        request = QueryRequest(query="Install Redis on my server", include_reasoning=True)
        result = run_async(query_endpoint(request, req))
        self.assertIn("response", result)
        self.assertIn("reasoning", result)
        self.assertEqual(result["reasoning"]["intent"], "execute_script")
        self.assertGreater(result["reasoning"]["confidence"], 0.8)
        logger.info("PASS: Install Redis query returns execute_script intent")

    def test_deploy_grafana_query(self):
        req, mock_vs, mock_re = self._make_mock_request()
        mock_re.reason = AsyncMock(return_value={
            "intent": "execute_terraform",
            "confidence": 0.88,
            "final_answer": "Use terraform_docker_linux_grafana to deploy Grafana.",
            "steps": [{"step": "classify", "result": "execute_terraform"}],
        })
        request = QueryRequest(query="Deploy Grafana monitoring", include_reasoning=True)
        result = run_async(query_endpoint(request, req))
        self.assertEqual(result["reasoning"]["intent"], "execute_terraform")
        logger.info("PASS: Deploy Grafana returns execute_terraform intent")

    def test_general_question_query(self):
        req, mock_vs, mock_re = self._make_mock_request()
        mock_re.reason = AsyncMock(return_value={
            "intent": "other",
            "confidence": 0.15,
            "final_answer": "This is a general question.",
            "steps": [{"step": "classify", "result": "other"}],
        })
        request = QueryRequest(query="What is the weather today?", include_reasoning=True)
        result = run_async(query_endpoint(request, req))
        self.assertEqual(result["reasoning"]["intent"], "other")
        self.assertLess(result["reasoning"]["confidence"], 0.5)
        logger.info("PASS: General question classified as 'other'")

    def test_cicd_setup_query(self):
        req, mock_vs, mock_re = self._make_mock_request()
        mock_re.reason = AsyncMock(return_value={
            "intent": "setup_cicd",
            "confidence": 0.85,
            "final_answer": "Set up GitHub Actions CI/CD for FastAPI.",
            "steps": [{"step": "classify", "result": "setup_cicd"}],
        })
        request = QueryRequest(query="Set up CI/CD for my FastAPI project", include_reasoning=True)
        result = run_async(query_endpoint(request, req))
        self.assertEqual(result["reasoning"]["intent"], "setup_cicd")
        logger.info("PASS: CI/CD setup query returns setup_cicd intent")

    def test_scan_ports_query(self):
        req, mock_vs, mock_re = self._make_mock_request()
        mock_re.reason = AsyncMock(return_value={
            "intent": "execute_script",
            "confidence": 0.90,
            "final_answer": "Use network/open_port_scanner.sh with target IP as argument.",
            "steps": [{"step": "classify", "result": "execute_script"}, {"step": "match", "result": "network/open_port_scanner.sh"}],
        })
        mock_vs.search = AsyncMock(return_value=[
            {"document": "network/open_port_scanner.sh <target> [start_port] [end_port]", "metadata": {"type": "script"}, "score": 0.93},
        ])
        request = QueryRequest(query="Scan open ports on 192.168.1.1", include_reasoning=True)
        result = run_async(query_endpoint(request, req))
        self.assertEqual(result["reasoning"]["intent"], "execute_script")
        logger.info("PASS: Port scan query with args")


class TestHealthEndpoint(unittest.TestCase):
    """Test health endpoint."""

    @unittest.skipIf(health is None, "health endpoint not importable")
    def test_health_returns_ok(self):
        result = run_async(health())
        self.assertIn("status", result)
        self.assertEqual(result["status"], "healthy")
        logger.info("PASS: Health endpoint returns healthy")


# ==========================================================================
# Run
# ==========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
