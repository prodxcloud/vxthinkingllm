
import csv
import random
from datetime import datetime, timedelta

# Define the fieldnames for the CSV file
fieldnames = [
    "incident_id", "severity", "category", "service", "error_code",
    "description", "root_cause", "resolution", "prevention", "tags", "timestamp"
]

# Predefined lists of possible values for different fields
severities = ["critical", "high", "medium", "low"]
categories = [
    "deployment", "database", "infrastructure", "cicd", "networking",
    "security", "container", "api", "storage", "monitoring", "compute",
    "messaging", "deployment", "api", "container", "networking", "storage",
    "security", "cicd", "database", "infrastructure", "monitoring", "compute",
    "messaging"
]
services = [
    "kubernetes", "postgresql", "aws", "github-actions", "load-balancer",
    "iam", "docker", "gateway", "s3", "prometheus", "argocd", "redis",
    "lambda", "vpc", "jenkins", "certificates", "hpa", "kafka", "dynamodb",
    "terraform", "rest", "kubernetes", "dns", "ebs", "vault", "gitlab",
    "helm", "mysql", "aws", "datadog", "graphql", "registry", "ingress",
    "sqs", "blue-green", "waf", "mongodb", "vpn", "eks", "docker", "jwt",
    "efs", "pvc", "alertmanager", "canary", "elasticsearch", "cloudfront",
    "cloudtrail", "ecs", "sns", "rollback", "configmap", "rate-limiting",
    "cloudformation", "aurora", "transit-gateway", "kms", "sonarqube",
    "etcd", "glacier", "websocket", "feature-flag", "containerd", "grafana",
    "nat", "rds", "guardduty", "service", "rabbitmq", "artifact", "grpc",
    "spot", "istio", "nfs", "cassandra", "route53", "inspector", "crd",
    "openapi", "buildkit", "argo-rollouts", "loki", "privatelink",
    "memcached", "ssm", "tekton", "admission", "cors", "persistent-volume",
    "kustomize", "security-group", "timescaledb", "cognito", "kaniko",
    "service-mesh", "tempo", "flux", "ami", "envoy", "cockroachdb",
    "secrets-manager", "pod-disruption", "idempotency", "dagger", "cri-o",
    "victoriametrics", "network-policy", "patroni", "spinnaker", "trivy",
    "graphql-federation", "pulumi", "scheduler", "csi", "calico",
    "clickhouse", "falco", "buildkite", "keda", "oauth", "podman", "thanos",
    "cilium", "vitess", "opa", "keptn", "payload", "crossplane", "kubelet",
    "minio", "wireguard", "yugabytedb", "cert-manager", "circleci",

]
error_codes = [
    "CrashLoopBackOff", "FATAL", "EC2.InstanceLimitExceeded", "RUNNER_TIMEOUT",
    "502 Bad Gateway", "AccessDenied", "ImagePullBackOff",
    "429 Too Many Requests", "SlowDown", "ScrapeTimeout", "SyncFailed",
    "CLUSTERDOWN", "FunctionError", "NetworkInterfaceLimit", "BUILD_FAILURE",
    "SSL_HANDSHAKE_FAILURE", "FailedGetResourceMetric",
    "UnknownTopicOrPartition", "ProvisionedThroughputExceeded",
    "StateLockedError", "504 Gateway Timeout", "OOMKilled", "NXDOMAIN",
    "VolumeAttachmentTimeout", "SecretNotFound", "PipelineStuck",
    "ReleaseUpgradeFailed", "Lock wait timeout exceeded", "ServiceUnavailable",
    "AgentNotReporting", "QueryComplexityExceeded", "RegistryRateLimited",
    "IngressControllerDown", "MessageNotVisible", "TrafficShiftFailed",
    "FalsePositiveBlock", "ReplicaSetNotHealthy", "TunnelDown", "NodeNotReady",
    "BuildContextTooLarge", "JWTExpired", "MountTargetNotAvailable",
    "PVCPending", "AlertNotFiring", "CanaryFailed", "ClusterRed", "OriginError",
    "AuditLogMissing", "TaskFailedToStart", "DeliveryFailed", "RollbackFailed",
    "ConfigMapUpdateFailed", "BurstLimitExceeded", "StackUpdateRollback",
    "FailoverCompleted", "AttachmentFailed", "KeyDisabled", "QualityGateFailed",
    "EtcdClusterDegraded", "RetrievalTimeout", "ConnectionDropped",
    "FlagConfigError", "RuntimeError", "DashboardLoadFailed",
    "NATGatewayErrorPortAllocation", "StorageFull", "HighSeverityFinding",
    "EndpointNotReady", "QueueOverflow", "ArtifactExpired", "ServiceUnavailable",
    "SpotInterruption", "SidecarInjectionFailed", "MountStale", "NodeDown",
    "HealthCheckFailing", "CriticalVulnerability", "CustomResourceInvalid",
    "SchemaValidationFailed", "CacheMiss", "AnalysisFailed",

]

# Function to generate a single random incident
def generate_incident(incident_id):
    severity = random.choice(severities)
    category = random.choice(categories)
    service = random.choice(services)
    error = random.choice(error_codes)
    timestamp = datetime.now() - timedelta(days=random.randint(0, 365),
                                            hours=random.randint(0, 23),
                                            minutes=random.randint(0, 59))

    return {
        "incident_id": f"INC-{incident_id:03d}",
        "severity": severity,
        "category": category,
        "service": service,
        "error_code": error,
        "description": f"Service {service} in {category} experiencing {error} errors.",
        "root_cause": f"Root cause for {error} is under investigation.",
        "resolution": f"Resolving {error} by restarting the service.",
        "prevention": f"Implementing monitoring for {service} to prevent future {error} issues.",
        "tags": f"{service}+{category}+{severity}",
        "timestamp": timestamp.isoformat() + "Z",
    }

# Main function to generate and append incidents
def main():
    num_incidents = 1500
    # Read existing incident IDs to avoid duplicates
    existing_ids = set()
    try:
        with open("C:/Users/WemboOtepaMulumba/OneDrive - Nathalie Babineau/Desktop/research/LLM_AI_LAB/va_llm_v1/app/data/cloud_incidents.csv", "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if "incident_id" in row:
                    existing_ids.add(int(row["incident_id"].split("-")[1]))
    except FileNotFoundError:
        # File doesn't exist, so we'll create it
        with open("C:/Users/WemboOtepaMulumba/OneDrive - Nathalie Babineau/Desktop/research/LLM_AI_LAB/va_llm_v1/app/data/cloud_incidents.csv", "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    # Determine the starting ID for new incidents
    start_id = max(existing_ids) + 1 if existing_ids else 1

    # Generate and append new incidents
    with open("C:/Users/WemboOtepaMulumba/OneDrive - Nathalie Babineau/Desktop/research/LLM_AI_LAB/va_llm_v1/app/data/cloud_incidents.csv", "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for i in range(start_id, start_id + num_incidents):
            incident = generate_incident(i)
            writer.writerow(incident)

    print(f"Appended {num_incidents} new incidents to cloud_incidents.csv")

if __name__ == "__main__":
    main()
