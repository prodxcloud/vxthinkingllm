#!/usr/bin/env python3
"""
Generate cloud_deployments.csv for LLM training (va_llm_v1) and InfinityAI cloud agent.

Schema aligns with GolangInfrastructure:
- VM: EC2ProvisionRequest (vm.go)
- Kubernetes: ClusterProvisionRequest (kubernetes.go) - cluster_name, node_count, node_type, region, cloud_provider
- Docker: ContainerDeployRequest (dockerservices/container.go) - image, container_name, ports, hostname, username, key_pair_name
- FastAPI: FastAPIDeployRequest (fastapi.go) - hostname, ssh_username, username, key_pair_name, app_port, app_name
- Static website: StaticWebsiteDeployRequest (staticwebsite.go) - hostname, ssh_username, username, key_pair_name, server_name
- Database: MetalDBProvisionRequest (databases/metaldb.go) - hostname, username, key_pair_name, database_name, database_user, postgres_version

Run from va_llm_v1 root:
    python scripts/generate_cloud_deployments.py
Output: app/data/cloud_deployments.csv (default 2500 rows; set --rows for more).
"""

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# --- VM (EC2) ---
INSTANCE_TYPES = [
    "t2.micro", "t2.small", "t2.medium", "t2.large", "t2.xlarge",
    "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge",
    "m5.large", "m5.xlarge", "c5.large", "c6g.medium",
]
REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1",
]
CLOUD_PROVIDERS = ["aws", "azure", "gcp", "valtunox"]
OS_OPTIONS = ["ubuntu-22.04", "ubuntu-24.04", "ubuntu", "centos", "windows"]
VOLUME_SIZES_GB = [8, 20, 30, 40, 50, 100, 200, 500]
VOLUME_TYPES = ["gp2", "gp3", "standard"]
ENVIRONMENTS = ["dev", "staging", "prod"]
SIZE_TIERS = ["small", "medium", "large"]

# --- Kubernetes (ClusterProvisionRequest) ---
K8S_NODE_TYPES = ["t3.medium", "t3.large", "m5.large", "m5.xlarge"]
K8S_VERSIONS = ["1.28", "1.29", "1.30", "1.31"]

# --- Docker (ContainerDeployRequest / service name from dockerservices.go) ---
DOCKER_SERVICES = [
    "nginx", "redis", "postgres", "mysql", "mongodb", "rabbitmq", "portainer",
    "grafana", "n8n", "jenkins", "gitea", "elasticsearch", "kafka", "vault",
]
DOCKER_IMAGES = [
    "nginx:latest", "redis:alpine", "postgres:15", "mysql:8", "rabbitmq:3-management",
    "grafana/grafana:latest", "portainer/portainer-ce:latest",
]
PORTS_EXAMPLES = ["80:80", "6379:6379", "5432:5432", "8000:8000", "3000:3000", "8080:8080"]

# --- FastAPI / Static (hostname = target VM) ---
APP_PORTS = ["8000", "8080", "3000"]
HTTP_PORTS = ["80", "443", "8080"]

# --- Database (MetalDB: postgres on VM) ---
DATABASE_ENGINES = ["postgres", "postgresql", "mysql"]
POSTGRES_VERSIONS = ["14", "15", "16"]
DB_PORTS = ["5432", "3306", "27017"]

# All intents we generate
INTENTS = ["provision_vm", "provision_kubernetes", "provision_docker", "provision_fastapi", "provision_static_website", "provision_database"]

# Prompt templates per intent (with optional placeholders)
VM_PROMPTS = [
    "Deploy an EC2 instance with {volume_size_gb}GB storage, {instance_type}",
    "Create a {size_tier} size VM in {region}",
    "I need a {instance_type} instance, {volume_size_gb}GB disk, {os}",
    "Provision {cloud_provider} VM: {instance_type}, {volume_size_gb}GB, {region}",
    "Deploy EC2 {instance_type} with {volume_size_gb}GB",
    "Spin up a {size_tier} server on {cloud_provider} in {region}",
    "Deploy ec2 instance 30gb t2 micro",
    "Medium size EC2 in us-east-1",
    "Small Ubuntu server, 20GB",
    "Provision valtunox VM with default settings",
]
K8S_PROMPTS = [
    "Deploy a Kubernetes cluster in {region} with {node_count} nodes",
    "Create an EKS cluster, {node_count} nodes, {node_type}",
    "I need a K8s cluster on {cloud_provider}, {region}, medium size",
    "Provision Kubernetes cluster: {cluster_name}, {node_count} nodes",
    "Deploy EKS cluster with {node_count} worker nodes",
    "Create GKE cluster in {region}",
    "Deploy a new Kubernetes cluster",
    "Set up AKS cluster, 3 nodes",
]
DOCKER_PROMPTS = [
    "Deploy {docker_service} container on my VM",
    "Run a {docker_service} Docker container",
    "I need {docker_service} as a container, port {ports}",
    "Deploy Docker image {docker_image}",
    "Spin up {docker_service} container",
    "Run nginx in Docker",
    "Deploy Redis container",
    "Start a PostgreSQL container with port 5432",
]
FASTAPI_PROMPTS = [
    "Deploy my FastAPI app to hostname {hostname}",
    "Deploy FastAPI application, app port {app_port}",
    "I want to deploy a FastAPI app on my VM",
    "Deploy FastAPI to {hostname}, port {app_port}",
]
STATIC_PROMPTS = [
    "Deploy static website to {hostname}",
    "Deploy static HTML site to my server",
    "I need to deploy a static website, nginx, port 80",
    "Deploy static website to nginx on {hostname}",
]
DB_PROMPTS = [
    "Provision PostgreSQL database on {hostname}",
    "Deploy Postgres database, version {postgres_version}",
    "I need a PostgreSQL database on my VM",
    "Set up MySQL database",
    "Provision database: {database_engine}, name {database_name}",
]

SIZE_TO_DEFAULTS = {
    "small": [("t2.micro", 8), ("t3.micro", 20)],
    "medium": [("t2.medium", 30), ("t3.medium", 40)],
    "large": [("t2.xlarge", 100), ("m5.large", 200)],
}


def _str(v):
    return "" if v is None else str(v)


def generate_vm_row(idx: int, start_date: datetime) -> dict:
    base = {"deployment_id": f"DEP-{idx:05d}", "intent": "provision_vm"}
    instance_type = random.choice(INSTANCE_TYPES)
    region = random.choice(REGIONS)
    cloud_provider = random.choice(CLOUD_PROVIDERS)
    os_name = random.choice(OS_OPTIONS)
    volume_size_gb = random.choice(VOLUME_SIZES_GB)
    volume_type = random.choice(VOLUME_TYPES)
    environment = random.choice(ENVIRONMENTS)
    size_tier = random.choice(SIZE_TIERS)
    username = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    workspace = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    instance_name = f"vm-{random.randint(1, 9999)}" if random.random() < 0.4 else ""
    if size_tier and random.random() < 0.5:
        opts = SIZE_TO_DEFAULTS.get(size_tier, SIZE_TO_DEFAULTS["medium"])
        instance_type, volume_size_gb = random.choice(opts)
    tpl = random.choice(VM_PROMPTS)
    try:
        prompt = tpl.format(
            instance_type=instance_type, region=region, cloud_provider=cloud_provider,
            os=os_name, volume_size_gb=volume_size_gb, size_tier=size_tier,
            username=username or "joeuser", workspace=workspace or "default-ws",
        )
    except KeyError:
        prompt = tpl
    base["prompt"] = prompt
    base["username"] = username
    base["workspace"] = workspace
    base["instance_name"] = instance_name
    base["instance_type"] = instance_type
    base["region"] = region
    base["cloud_provider"] = cloud_provider
    base["os"] = os_name
    base["volume_size_gb"] = volume_size_gb
    base["volume_type"] = volume_type
    base["environment"] = environment
    base["size_tier"] = size_tier
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    # Empty for VM-only
    base["cluster_name"] = base["node_count"] = base["node_type"] = base["kubernetes_version"] = ""
    base["docker_image"] = base["docker_service"] = base["container_name"] = base["ports"] = ""
    base["hostname"] = base["ssh_username"] = base["key_pair_name"] = ""
    base["app_name"] = base["app_port"] = base["http_port"] = base["https_port"] = base["server_name"] = ""
    base["database_engine"] = base["database_name"] = base["database_user"] = base["postgres_version"] = base["port"] = ""
    return base


def generate_k8s_row(idx: int, start_date: datetime) -> dict:
    base = {"deployment_id": f"DEP-{idx:05d}", "intent": "provision_kubernetes"}
    cluster_name = f"cluster-{random.randint(1, 999)}"
    node_count = random.choice([2, 3, 4, 5])
    node_type = random.choice(K8S_NODE_TYPES)
    region = random.choice(REGIONS)
    cloud_provider = random.choice(["aws", "gcp", "azure"])
    environment = random.choice(ENVIRONMENTS)
    kubernetes_version = random.choice(K8S_VERSIONS)
    username = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    workspace = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    tpl = random.choice(K8S_PROMPTS)
    try:
        prompt = tpl.format(
            region=region, node_count=node_count, node_type=node_type,
            cloud_provider=cloud_provider, cluster_name=cluster_name,
        )
    except KeyError:
        prompt = tpl
    base["prompt"] = prompt
    base["username"] = username
    base["workspace"] = workspace
    base["cluster_name"] = cluster_name
    base["node_count"] = node_count
    base["node_type"] = node_type
    base["region"] = region
    base["cloud_provider"] = cloud_provider
    base["environment"] = environment
    base["kubernetes_version"] = kubernetes_version
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    base["instance_name"] = base["instance_type"] = base["os"] = base["volume_size_gb"] = base["volume_type"] = base["size_tier"] = ""
    base["docker_image"] = base["docker_service"] = base["container_name"] = base["ports"] = ""
    base["hostname"] = base["ssh_username"] = base["key_pair_name"] = ""
    base["app_name"] = base["app_port"] = base["http_port"] = base["https_port"] = base["server_name"] = ""
    base["database_engine"] = base["database_name"] = base["database_user"] = base["postgres_version"] = base["port"] = ""
    return base


def generate_docker_row(idx: int, start_date: datetime) -> dict:
    base = {"deployment_id": f"DEP-{idx:05d}", "intent": "provision_docker"}
    use_service = random.random() < 0.6
    if use_service:
        docker_service = random.choice(DOCKER_SERVICES)
        docker_image = ""
        container_name = f"{docker_service}-{random.randint(1, 99)}"
        ports = random.choice(PORTS_EXAMPLES)
    else:
        docker_image = random.choice(DOCKER_IMAGES)
        docker_service = docker_image.split("/")[-1].split(":")[0] if "/" in docker_image else docker_image.split(":")[0]
        container_name = f"{docker_service}-{random.randint(1, 99)}"
        ports = random.choice(PORTS_EXAMPLES)
    username = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    workspace = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    hostname = f"vm-{random.randint(1, 999)}.example.com" if random.random() < 0.5 else ""
    tpl = random.choice(DOCKER_PROMPTS)
    try:
        prompt = tpl.format(docker_service=docker_service, docker_image=docker_image or docker_service, ports=ports)
    except KeyError:
        prompt = tpl
    base["prompt"] = prompt
    base["username"] = username
    base["workspace"] = workspace
    base["docker_image"] = docker_image or docker_service
    base["docker_service"] = docker_service
    base["container_name"] = container_name
    base["ports"] = ports
    base["hostname"] = hostname
    base["ssh_username"] = "ubuntu" if hostname else ""
    base["key_pair_name"] = f"key-{random.randint(1, 99)}" if hostname else ""
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    base["instance_name"] = base["instance_type"] = base["region"] = base["os"] = base["volume_size_gb"] = base["volume_type"] = base["environment"] = base["size_tier"] = ""
    base["cluster_name"] = base["node_count"] = base["node_type"] = base["kubernetes_version"] = ""
    base["app_name"] = base["app_port"] = base["http_port"] = base["https_port"] = base["server_name"] = ""
    base["database_engine"] = base["database_name"] = base["database_user"] = base["postgres_version"] = base["port"] = ""
    return base


def generate_fastapi_row(idx: int, start_date: datetime) -> dict:
    base = {"deployment_id": f"DEP-{idx:05d}", "intent": "provision_fastapi"}
    hostname = f"app-{random.randint(1, 999)}.example.com"
    app_port = random.choice(APP_PORTS)
    username = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    workspace = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    tpl = random.choice(FASTAPI_PROMPTS)
    prompt = tpl.format(hostname=hostname, app_port=app_port)
    base["prompt"] = prompt
    base["username"] = username
    base["workspace"] = workspace
    base["hostname"] = hostname
    base["ssh_username"] = "ubuntu"
    base["key_pair_name"] = f"app-{random.randint(1, 99)}"
    base["app_name"] = f"fastapi-app-{random.randint(1, 99)}"
    base["app_port"] = app_port
    base["http_port"] = random.choice(HTTP_PORTS)
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    base["instance_name"] = base["instance_type"] = base["region"] = base["cloud_provider"] = base["os"] = ""
    base["volume_size_gb"] = base["volume_type"] = base["environment"] = base["size_tier"] = ""
    base["cluster_name"] = base["node_count"] = base["node_type"] = base["kubernetes_version"] = ""
    base["docker_image"] = base["docker_service"] = base["container_name"] = base["ports"] = ""
    base["https_port"] = base["server_name"] = ""
    base["database_engine"] = base["database_name"] = base["database_user"] = base["postgres_version"] = base["port"] = ""
    return base


def generate_static_row(idx: int, start_date: datetime) -> dict:
    base = {"deployment_id": f"DEP-{idx:05d}", "intent": "provision_static_website"}
    hostname = f"web-{random.randint(1, 999)}.example.com"
    server_name = f"www.site-{random.randint(1, 99)}.com" if random.random() < 0.5 else ""
    username = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    workspace = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    tpl = random.choice(STATIC_PROMPTS)
    prompt = tpl.format(hostname=hostname)
    base["prompt"] = prompt
    base["username"] = username
    base["workspace"] = workspace
    base["hostname"] = hostname
    base["ssh_username"] = "ubuntu"
    base["key_pair_name"] = f"web-{random.randint(1, 99)}"
    base["http_port"] = "80"
    base["https_port"] = "443" if random.random() < 0.5 else ""
    base["server_name"] = server_name
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    base["instance_name"] = base["instance_type"] = base["region"] = base["cloud_provider"] = base["os"] = ""
    base["volume_size_gb"] = base["volume_type"] = base["environment"] = base["size_tier"] = ""
    base["cluster_name"] = base["node_count"] = base["node_type"] = base["kubernetes_version"] = ""
    base["docker_image"] = base["docker_service"] = base["container_name"] = base["ports"] = ""
    base["app_name"] = base["app_port"] = ""
    base["database_engine"] = base["database_name"] = base["database_user"] = base["postgres_version"] = base["port"] = ""
    return base


def generate_database_row(idx: int, start_date: datetime) -> dict:
    base = {"deployment_id": f"DEP-{idx:05d}", "intent": "provision_database"}
    database_engine = random.choice(DATABASE_ENGINES)
    database_name = f"db_{random.randint(1, 999)}"
    database_user = f"dbuser{random.randint(1, 99)}"
    postgres_version = random.choice(POSTGRES_VERSIONS) if database_engine in ("postgres", "postgresql") else ""
    port = random.choice(DB_PORTS)
    hostname = f"db-{random.randint(1, 999)}.example.com"
    username = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    workspace = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    tpl = random.choice(DB_PROMPTS)
    try:
        prompt = tpl.format(hostname=hostname, postgres_version=postgres_version, database_engine=database_engine, database_name=database_name)
    except KeyError:
        prompt = tpl
    base["prompt"] = prompt
    base["username"] = username
    base["workspace"] = workspace
    base["hostname"] = hostname
    base["ssh_username"] = "ubuntu"
    base["key_pair_name"] = f"db-{random.randint(1, 99)}"
    base["database_engine"] = database_engine
    base["database_name"] = database_name
    base["database_user"] = database_user
    base["postgres_version"] = postgres_version
    base["port"] = port
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    base["instance_name"] = base["instance_type"] = base["region"] = base["cloud_provider"] = base["os"] = ""
    base["volume_size_gb"] = base["volume_type"] = base["environment"] = base["size_tier"] = ""
    base["cluster_name"] = base["node_count"] = base["node_type"] = base["kubernetes_version"] = ""
    base["docker_image"] = base["docker_service"] = base["container_name"] = base["ports"] = ""
    base["app_name"] = base["app_port"] = base["http_port"] = base["https_port"] = base["server_name"] = ""
    return base


def generate_row(idx: int, start_date: datetime) -> dict:
    intent_choice = random.choices(
        INTENTS,
        weights=[40, 15, 20, 8, 7, 10],  # VM most, then docker, k8s, db, fastapi, static
    )[0]
    if intent_choice == "provision_vm":
        return generate_vm_row(idx, start_date)
    if intent_choice == "provision_kubernetes":
        return generate_k8s_row(idx, start_date)
    if intent_choice == "provision_docker":
        return generate_docker_row(idx, start_date)
    if intent_choice == "provision_fastapi":
        return generate_fastapi_row(idx, start_date)
    if intent_choice == "provision_static_website":
        return generate_static_row(idx, start_date)
    if intent_choice == "provision_database":
        return generate_database_row(idx, start_date)
    return generate_vm_row(idx, start_date)


FIELDNAMES = [
    "deployment_id", "prompt", "intent", "username", "workspace",
    "instance_name", "instance_type", "region", "cloud_provider", "os",
    "volume_size_gb", "volume_type", "environment", "size_tier",
    "cluster_name", "node_count", "node_type", "kubernetes_version",
    "docker_image", "docker_service", "container_name", "ports",
    "hostname", "ssh_username", "key_pair_name",
    "app_name", "app_port", "http_port", "https_port", "server_name",
    "database_engine", "database_name", "database_user", "postgres_version", "port",
    "date",
]


def main():
    parser = argparse.ArgumentParser(description="Generate cloud_deployments.csv for LLM training")
    parser.add_argument("--rows", type=int, default=2500, help="Number of rows (default 2500)")
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "app" / "data" / "cloud_deployments.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start_date = datetime.now()

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for i in range(args.rows):
            row = generate_row(i, start_date)
            # Ensure all keys exist and are strings for CSV
            out = {k: _str(row.get(k, "")) for k in FIELDNAMES}
            writer.writerow(out)

    print(f"Wrote {args.rows} rows to {out_path}")


if __name__ == "__main__":
    main()
