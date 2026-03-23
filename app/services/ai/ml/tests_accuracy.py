"""
VaLLM Accuracy Test Harness - Comprehensive intent detection & payload accuracy tests.

Tests ALL 20+ intent types with varied natural language queries.
Measures: intent precision, payload completeness, entity extraction accuracy.
Produces a scoreboard report at the end.

Run:
    python -m pytest app/services/ai/ml/tests_accuracy.py -v --tb=short
    python -m pytest app/services/ai/ml/tests_accuracy.py -v -k "test_intent"
"""

import unittest
import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional

# Setup path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.ai.ml.cloud_routes import (
    _raw_to_golang_payload,
    _classify_non_provisioning,
    _is_deployment_result,
    _ensure_complete_payload,
)
from app.services.ai.ml.entity_extraction import EntityExtractor, extract_entities_from_query


# ==========================================================================
# SCOREBOARD - tracks results across all tests
# ==========================================================================
class Scoreboard:
    """Tracks test results for final report."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.results = defaultdict(lambda: {"pass": 0, "fail": 0, "details": []})
        return cls._instance

    def record(self, category: str, passed: bool, detail: str = ""):
        if passed:
            self.results[category]["pass"] += 1
        else:
            self.results[category]["fail"] += 1
            self.results[category]["details"].append(detail)

    def report(self) -> str:
        lines = ["\n" + "=" * 70, "VALLM ACCURACY SCOREBOARD", "=" * 70]
        total_pass = 0
        total_fail = 0
        for category, data in sorted(self.results.items()):
            p, f = data["pass"], data["fail"]
            total_pass += p
            total_fail += f
            total = p + f
            pct = (p / total * 100) if total > 0 else 0
            status = "PASS" if f == 0 else "WARN" if pct >= 80 else "FAIL"
            lines.append(f"  [{status}] {category:40s}  {p}/{total} ({pct:.0f}%)")
            for d in data["details"][:3]:  # show first 3 failures
                lines.append(f"         - {d}")
        lines.append("-" * 70)
        grand_total = total_pass + total_fail
        grand_pct = (total_pass / grand_total * 100) if grand_total > 0 else 0
        lines.append(f"  OVERALL: {total_pass}/{grand_total} ({grand_pct:.0f}%)")
        lines.append("=" * 70)
        return "\n".join(lines)


scoreboard = Scoreboard()


# ==========================================================================
# Test 1: Payload generation for ALL intent types
# ==========================================================================
class TestAllIntentPayloads(unittest.TestCase):
    """Test _raw_to_golang_payload produces correct fields for every intent."""

    def _test_payload(self, intent: str, raw: Dict, required_fields: List[str], category: str = "payload_generation"):
        payload = _raw_to_golang_payload(raw, intent)
        for field in required_fields:
            present = field in payload and payload[field] not in (None, "", 0)
            scoreboard.record(category, present, f"{intent}.{field} missing or empty")
            self.assertIn(field, payload, f"{intent} payload missing {field}")

    def test_provision_vm(self):
        raw = {"username": "joel", "instance_type": "t3.medium", "region": "us-west-2",
               "cloud_provider": "aws", "os": "ubuntu", "volume_size_gb": "50",
               "volume_type": "gp3", "environment": "production", "hostname": "web.prod.io"}
        self._test_payload("provision_vm", raw,
                           ["instance_type", "region", "cloud_provider", "os", "volume_size", "volume_type", "environment"])

    def test_provision_kubernetes(self):
        raw = {"cluster_name": "prod-eks", "node_count": "3", "node_type": "m5.large",
               "kubernetes_version": "1.29", "region": "us-east-1", "cloud_provider": "aws"}
        self._test_payload("provision_kubernetes", raw,
                           ["cluster_name", "node_count", "node_type", "kubernetes_version", "region"])

    def test_provision_docker(self):
        raw = {"docker_image": "nginx:latest", "container_name": "web-nginx", "ports": "80:80"}
        self._test_payload("provision_docker", raw, ["docker_image", "container_name", "ports"])

    def test_provision_database(self):
        raw = {"database_engine": "postgresql", "database_name": "analytics_db",
               "database_user": "admin", "port": "5432"}
        self._test_payload("provision_database", raw,
                           ["database_engine", "database_name", "database_user", "port"])

    def test_provision_fastapi(self):
        raw = {"hostname": "api.prod.com", "app_name": "billing-api", "app_port": "8000", "http_port": "80"}
        self._test_payload("provision_fastapi", raw, ["hostname", "app_name", "app_port", "http_port"])

    def test_provision_static_website(self):
        raw = {"hostname": "docs.example.com", "server_name": "docs.example.com", "http_port": "80"}
        self._test_payload("provision_static_website", raw, ["hostname", "server_name", "http_port"])

    def test_provision_nextjs(self):
        raw = {"hostname": "web.example.com", "app_name": "nextjs-app-1", "app_port": "3000",
               "http_port": "80", "runtime_version": "18", "repo_url": "https://github.com/org/app.git"}
        self._test_payload("provision_nextjs", raw, ["hostname", "app_name", "app_port", "framework", "node_version"])

    def test_provision_django(self):
        raw = {"hostname": "app.example.com", "app_name": "django-app-1", "app_port": "8000",
               "http_port": "80", "database_engine": "postgres", "runtime_version": "3.12"}
        self._test_payload("provision_django", raw,
                           ["hostname", "app_name", "app_port", "framework", "python_version", "database_engine"])

    def test_provision_reactjs(self):
        raw = {"hostname": "web.example.com", "app_name": "react-app-1", "app_port": "8080",
               "http_port": "80", "runtime_version": "22", "repo_url": "https://github.com/org/app.git"}
        self._test_payload("provision_reactjs", raw, ["hostname", "app_name", "app_port", "framework", "node_version"])

    def test_provision_monitoring(self):
        raw = {"hostname": "mon.example.com", "monitoring_tool": "prometheus", "monitoring_port": "9090"}
        self._test_payload("provision_monitoring", raw, ["hostname", "monitoring_tool", "monitoring_port"])

    def test_provision_elk(self):
        raw = {"hostname": "elk.example.com", "elk_version": "8.12.0", "es_port": "9200",
               "kibana_port": "5601", "logstash_port": "5044"}
        self._test_payload("provision_elk", raw, ["hostname", "elk_version", "es_port", "kibana_port"])

    def test_provision_vpn(self):
        raw = {"hostname": "vpn.example.com", "vpn_protocol": "wireguard", "vpn_port": "51820", "vpn_clients": "20"}
        self._test_payload("provision_vpn", raw, ["hostname", "vpn_protocol", "vpn_port", "vpn_clients"])

    def test_provision_cicd(self):
        raw = {"hostname": "cicd.example.com", "cicd_tool": "jenkins", "cicd_port": "8080",
               "docker_image": "jenkins/jenkins:lts"}
        self._test_payload("provision_cicd", raw, ["hostname", "cicd_tool", "cicd_port"])

    def test_provision_managed_database(self):
        raw = {"database_engine": "aurora-postgresql", "database_name": "managed-db-1",
               "db_instance_class": "db.r5.large", "storage_size_gb": "200",
               "region": "us-east-1", "cloud_provider": "aws", "multi_az": "true"}
        self._test_payload("provision_managed_database", raw,
                           ["database_engine", "database_name", "db_instance_class", "storage_size_gb"])

    def test_provision_cache(self):
        raw = {"hostname": "cache.example.com", "cache_engine": "redis", "cache_port": "6379",
               "cache_size_mb": "512", "replicas": "1"}
        self._test_payload("provision_cache", raw, ["hostname", "cache_engine", "cache_port", "cache_size_mb"])

    def test_provision_storage(self):
        raw = {"storage_backend": "s3", "bucket_name": "my-bucket", "region": "us-east-1",
               "cloud_provider": "aws", "storage_size_gb": "500"}
        self._test_payload("provision_storage", raw, ["storage_backend", "bucket_name", "storage_size_gb"])

    def test_provision_ssl(self):
        raw = {"hostname": "secure.example.com", "domain_name": "secure.example.com", "ssl_provider": "letsencrypt"}
        self._test_payload("provision_ssl", raw, ["hostname", "domain_name", "ssl_provider"])

    def test_provision_loadbalancer(self):
        raw = {"hostname": "lb.example.com", "lb_type": "nginx", "lb_algorithm": "round-robin"}
        self._test_payload("provision_loadbalancer", raw, ["hostname", "lb_type", "lb_algorithm"])

    def test_provision_wordpress(self):
        raw = {"hostname": "blog.example.com", "app_name": "wordpress", "http_port": "80",
               "database_engine": "mysql"}
        self._test_payload("provision_wordpress", raw, ["hostname", "app_name", "http_port", "database_engine"])

    def test_provision_springboot(self):
        raw = {"hostname": "api.example.com", "app_name": "springboot-api", "app_port": "8080",
               "http_port": "80", "runtime_version": "17", "repo_url": "https://github.com/org/app.git"}
        self._test_payload("provision_springboot", raw, ["hostname", "app_name", "app_port", "framework", "java_version"])

    def test_provision_serverless(self):
        raw = {"function_name": "my-func", "runtime": "python3.12", "cloud_provider": "aws", "region": "us-east-1"}
        self._test_payload("provision_serverless", raw, ["function_name", "runtime", "cloud_provider"])

    def test_provision_cdn(self):
        raw = {"distribution_name": "my-cdn", "origin": "origin.example.com", "cloud_provider": "aws"}
        self._test_payload("provision_cdn", raw, ["distribution_name", "origin", "cloud_provider"])

    def test_provision_network(self):
        raw = {"vpc_name": "prod-vpc", "cidr_block": "10.0.0.0/16", "region": "us-east-1"}
        self._test_payload("provision_network", raw, ["vpc_name", "cidr_block", "region"])

    def test_provision_backup(self):
        raw = {"backup_target": "db-prod", "schedule": "daily", "retention_days": "30"}
        self._test_payload("provision_backup", raw, ["backup_target", "schedule", "retention_days"])


# ==========================================================================
# Test 2: Entity extraction accuracy across cloud providers
# ==========================================================================
class TestEntityExtractionAccuracy(unittest.TestCase):
    """Test entity extraction with varied, realistic queries."""

    def setUp(self):
        self.extractor = EntityExtractor()

    def _check(self, query: str, expected: Dict[str, str], category: str = "entity_extraction"):
        entities = self.extractor.extract_entities(query)
        for key, expected_val in expected.items():
            actual = entities.get(key, "")
            passed = str(actual).lower() == str(expected_val).lower()
            scoreboard.record(category, passed,
                              f"query='{query[:50]}' key={key} expected={expected_val} got={actual}")
            self.assertEqual(str(actual).lower(), str(expected_val).lower(),
                             f"Entity '{key}' mismatch for: {query}")

    # AWS instance types
    def test_aws_t3_medium(self):
        self._check("Deploy t3.medium in us-east-1", {"instance_type": "t3.medium", "region": "us-east-1"})

    def test_aws_t4g_small(self):
        self._check("Launch t4g.small ARM instance", {"instance_type": "t4g.small"})

    def test_aws_m6i_large(self):
        self._check("Create m6i.large for production", {"instance_type": "m6i.large"})

    def test_aws_c6g_medium(self):
        self._check("Provision c6g.medium graviton instance", {"instance_type": "c6g.medium"})

    def test_aws_r5_xlarge(self):
        self._check("I need r5.xlarge for high-memory workload", {"instance_type": "r5.xlarge"})

    # GCP instance types
    def test_gcp_n2_standard(self):
        self._check("Deploy n2-standard-4 on GCP", {"instance_type": "n2-standard-4", "cloud_provider": "gcp"})

    def test_gcp_e2_medium(self):
        self._check("Create e2-medium compute instance on Google Cloud",
                     {"instance_type": "e2-medium", "cloud_provider": "gcp"})

    # Azure instance types
    def test_azure_standard(self):
        self._check("Provision Standard_B2s VM on Azure",
                     {"instance_type": "Standard_B2s", "cloud_provider": "azure"})

    # RDS instance classes
    def test_rds_instance(self):
        self._check("Create db.r5.large RDS instance", {"instance_type": "db.r5.large"})

    # Regions
    def test_region_ca_central(self):
        self._check("Deploy in ca-central-1", {"region": "ca-central-1"})

    def test_region_sa_east(self):
        self._check("Launch VM in sa-east-1", {"region": "sa-east-1"})

    def test_region_ap_south(self):
        self._check("Create instance in ap-south-1", {"region": "ap-south-1"})

    def test_region_eu_north(self):
        self._check("Deploy to eu-north-1", {"region": "eu-north-1"})

    # Cloud provider detection
    def test_detect_aws(self):
        self._check("Deploy an EC2 instance", {"cloud_provider": "aws"})

    def test_detect_gcp(self):
        self._check("Create a GKE cluster", {"cloud_provider": "gcp"})

    def test_detect_azure(self):
        self._check("Provision Azure VM in West Europe", {"cloud_provider": "azure"})

    # Database engine detection
    def test_detect_postgres(self):
        self._check("Set up PostgreSQL database", {"database_engine": "postgresql"})

    def test_detect_mysql(self):
        self._check("Deploy MySQL database on port 3306", {"database_engine": "mysql"})

    def test_detect_mariadb(self):
        self._check("Create MariaDB instance", {"database_engine": "mariadb"})

    def test_detect_mongodb(self):
        self._check("Deploy MongoDB cluster", {"database_engine": "mongodb"})

    # Monitoring tool detection
    def test_detect_prometheus(self):
        self._check("Set up prometheus monitoring", {"monitoring_tool": "prometheus"})

    def test_detect_grafana(self):
        self._check("Deploy grafana dashboard", {"monitoring_tool": "grafana"})

    def test_detect_zabbix(self):
        self._check("Provision zabbix for monitoring", {"monitoring_tool": "zabbix"})

    # CICD tool detection
    def test_detect_jenkins(self):
        self._check("Deploy jenkins CI server", {"cicd_tool": "jenkins"})

    def test_detect_argocd(self):
        self._check("Set up argocd pipeline", {"cicd_tool": "argocd"})

    # VPN protocol detection
    def test_detect_wireguard(self):
        self._check("Deploy wireguard VPN", {"vpn_protocol": "wireguard"})

    def test_detect_openvpn(self):
        self._check("Set up openvpn server", {"vpn_protocol": "openvpn"})

    # OS detection
    def test_detect_ubuntu_24(self):
        self._check("Deploy with ubuntu-24.04", {"os": "ubuntu-24.04"})

    def test_detect_debian(self):
        self._check("Launch debian-12 instance", {"os": "debian-12"})

    def test_detect_amazon_linux(self):
        self._check("Create amazon-linux-2 VM", {"os": "amazon-linux-2"})

    # Hostname extraction
    def test_hostname_complex(self):
        self._check("Deploy FastAPI on api.staging.mycompany.com", {"hostname": "api.staging.mycompany.com"})

    def test_hostname_simple(self):
        self._check("Host website on docs.example.com", {"hostname": "docs.example.com"})

    # Port extraction
    def test_port_mapping(self):
        entities = self.extractor.extract_entities("Run container ports 8080:8080")
        passed = entities.get("ports") == "8080:8080"
        scoreboard.record("entity_extraction", passed, f"ports expected=8080:8080 got={entities.get('ports')}")

    # Storage extraction
    def test_storage_50gb(self):
        entities = self.extractor.extract_entities("Create VM with 50GB disk")
        passed = entities.get("volume_size_gb") == "50"
        scoreboard.record("entity_extraction", passed, f"volume expected=50 got={entities.get('volume_size_gb')}")

    # Docker image extraction
    def test_docker_nginx(self):
        entities = self.extractor.extract_entities("Run nginx container")
        passed = "nginx" in str(entities.get("docker_image", ""))
        scoreboard.record("entity_extraction", passed, f"image expected=nginx got={entities.get('docker_image')}")

    def test_docker_redis_alpine(self):
        entities = self.extractor.extract_entities("Deploy redis:alpine container")
        passed = "redis" in str(entities.get("docker_image", ""))
        scoreboard.record("entity_extraction", passed, f"image expected=redis got={entities.get('docker_image')}")


# ==========================================================================
# Test 3: Payload completeness with _ensure_complete_payload
# ==========================================================================
class TestPayloadCompleteness(unittest.TestCase):
    """Test that _ensure_complete_payload fills all required defaults."""

    def _check_complete(self, intent: str, initial_payload: Dict, raw: Dict,
                        required_fields: List[str], category: str = "payload_completeness"):
        result = _ensure_complete_payload(initial_payload, intent, raw)
        for field in required_fields:
            present = field in result and result[field] not in (None, "")
            scoreboard.record(category, present, f"{intent}.{field} not completed")

    def test_vm_defaults_from_empty(self):
        self._check_complete("provision_vm", {"username": "test"}, {},
                             ["instance_type", "region", "cloud_provider", "os", "volume_size",
                              "volume_type", "environment", "instance_name", "ssh_username"])

    def test_kubernetes_defaults(self):
        self._check_complete("provision_kubernetes", {"username": "test"}, {},
                             ["cluster_name", "node_count", "node_type", "kubernetes_version"])

    def test_docker_defaults(self):
        self._check_complete("provision_docker", {"username": "test"}, {},
                             ["docker_image", "container_name", "ports"])

    def test_database_defaults(self):
        self._check_complete("provision_database", {"username": "test"}, {},
                             ["database_engine", "database_name", "database_user", "port"])

    def test_nextjs_defaults(self):
        self._check_complete("provision_nextjs", {"username": "test"}, {},
                             ["app_name", "app_port", "http_port"])

    def test_django_defaults(self):
        self._check_complete("provision_django", {"username": "test"}, {},
                             ["app_name", "app_port", "http_port", "python_version", "database_engine"])

    def test_monitoring_defaults(self):
        self._check_complete("provision_monitoring", {"username": "test"}, {},
                             ["monitoring_tool", "monitoring_port"])

    def test_elk_defaults(self):
        self._check_complete("provision_elk", {"username": "test"}, {},
                             ["elk_version", "es_port", "kibana_port", "logstash_port"])

    def test_vpn_defaults(self):
        self._check_complete("provision_vpn", {"username": "test"}, {},
                             ["vpn_protocol", "vpn_port", "vpn_clients"])

    def test_cicd_defaults(self):
        self._check_complete("provision_cicd", {"username": "test"}, {},
                             ["cicd_tool", "cicd_port"])

    def test_managed_database_defaults(self):
        self._check_complete("provision_managed_database", {"username": "test"}, {},
                             ["database_engine", "database_name", "db_instance_class", "storage_size_gb"])

    def test_cache_defaults(self):
        self._check_complete("provision_cache", {"username": "test"}, {},
                             ["cache_engine", "cache_port", "cache_size_mb"])

    def test_storage_defaults(self):
        self._check_complete("provision_storage", {"username": "test"}, {},
                             ["storage_backend", "bucket_name", "storage_size_gb"])

    def test_ssl_defaults(self):
        self._check_complete("provision_ssl", {"username": "test", "hostname": "secure.example.com"}, {},
                             ["ssl_provider"])

    def test_loadbalancer_defaults(self):
        self._check_complete("provision_loadbalancer", {"username": "test"}, {},
                             ["lb_type", "lb_algorithm"])

    def test_wordpress_defaults(self):
        self._check_complete("provision_wordpress", {"username": "test"}, {},
                             ["app_name", "http_port", "database_engine"])

    def test_springboot_defaults(self):
        self._check_complete("provision_springboot", {"username": "test"}, {},
                             ["app_name", "app_port", "http_port", "java_version"])


# ==========================================================================
# Test 4: Deployment result detection (edge cases)
# ==========================================================================
class TestDeploymentDetectionEdgeCases(unittest.TestCase):
    """Extended edge-case tests for _is_deployment_result."""

    def test_all_intents_detected(self):
        """Every known intent should be detected as deployment."""
        intents = [
            "provision_vm", "provision_kubernetes", "provision_docker",
            "provision_database", "provision_fastapi", "provision_static_website",
            "provision_nextjs", "provision_django", "provision_reactjs",
            "provision_monitoring", "provision_elk", "provision_vpn",
            "provision_cicd", "provision_managed_database", "provision_cache",
            "provision_storage", "provision_ssl", "provision_loadbalancer",
            "provision_wordpress", "provision_springboot",
        ]
        for intent in intents:
            meta = {"raw": {"intent": intent, "prompt": f"Test {intent}"}}
            passed = _is_deployment_result(meta)
            scoreboard.record("deployment_detection", passed, f"{intent} not detected")
            self.assertTrue(passed, f"{intent} should be detected as deployment")


# ==========================================================================
# Test 5: Non-provisioning queries should return "other"
# ==========================================================================
class TestNonProvisioningClassification(unittest.TestCase):
    """Verify non-provisioning queries are not misclassified."""

    def test_non_provisioning_queries(self):
        queries = [
            "What is the weather today?",
            "How much does AWS cost per month?",
            "Show me billing dashboard",
            "Our API is throwing 503 errors",
            "Check server health status",
            "What is Kubernetes?",
            "Help me debug this Python error",
            "List all running processes",
        ]
        for q in queries:
            result = _classify_non_provisioning(q)
            passed = result == "other"
            scoreboard.record("non_provisioning", passed, f"'{q[:40]}' classified as {result}")
            self.assertEqual(result, "other")


# ==========================================================================
# Print scoreboard after all tests
# ==========================================================================
class TestZZZScoreboard(unittest.TestCase):
    """Print final scoreboard (runs last due to ZZZ prefix)."""

    def test_print_scoreboard(self):
        report = scoreboard.report()
        print(report)
        # Assert overall accuracy > 80%
        total_pass = sum(d["pass"] for d in scoreboard.results.values())
        total_fail = sum(d["fail"] for d in scoreboard.results.values())
        total = total_pass + total_fail
        if total > 0:
            accuracy = total_pass / total * 100
            self.assertGreaterEqual(accuracy, 80.0,
                                    f"Overall accuracy {accuracy:.0f}% is below 80% threshold")


if __name__ == "__main__":
    unittest.main(verbosity=2)
