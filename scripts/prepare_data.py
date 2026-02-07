#!/usr/bin/env python3
"""
Prepare cloud_deployments.csv for VaLLM provisioning training (5000 rows by default).

- Generates synthetic deployment rows for all 6 intents (VM, Kubernetes, Docker, FastAPI, static website, database).
- Uses many prompt variants and trainable facts for better intent/slot accuracy.
- Adds endpoint_url and payload (Golang provisioner API) per row.

Run from va_llm_v1 root:
    python scripts/prepare_data.py
    python scripts/prepare_data.py --rows 5000 --output app/data/datasets/cloud_deployments.csv
"""

import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# VM (EC2)
# ---------------------------------------------------------------------------
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

VM_PROMPTS = [
    "Deploy an EC2 instance with {volume_size_gb}GB storage, {instance_type}",
    "Create a {size_tier} size VM in {region}",
    "I need a {instance_type} instance, {volume_size_gb}GB disk, {os}",
    "Provision {cloud_provider} VM: {instance_type}, {volume_size_gb}GB, {region}",
    "Deploy EC2 {instance_type} with {volume_size_gb}GB",
    "Spin up a {size_tier} server on {cloud_provider} in {region}",
    "Deploy ec2 instance 30gb t2 micro",
    "Deploy EC2 instance t3.medium 50GB gp3 Ubuntu in us-west-2",
    "Medium size EC2 in us-east-1",
    "Small Ubuntu server, 20GB",
    "Provision valtunox VM with default settings",
    "Launch a {instance_type} VM in {region} with {os}",
    "I want to provision a {cloud_provider} virtual machine, {instance_type}, {volume_size_gb}GB {volume_type}",
    "Set up EC2 {instance_type} in {region}, {volume_size_gb}GB root volume",
    "Create VM: {instance_type}, {region}, {os}, {volume_size_gb}GB",
    "Please deploy an EC2 instance with {volume_size_gb}GB and {instance_type}",
    "Need a {size_tier} EC2 in {region} for {environment}",
    "Deploy a small EC2 instance with 30GB disk in us-east-1 with Ubuntu",
    "Provision aws VM: {instance_type}, {volume_size_gb}GB, {region}",
    "Provision azure VM: {instance_type}, {volume_size_gb}GB, {region}",
]

# ---------------------------------------------------------------------------
# Kubernetes (EKS/GKE/AKS)
# ---------------------------------------------------------------------------
K8S_NODE_TYPES = ["t3.medium", "t3.large", "m5.large", "m5.xlarge"]
K8S_VERSIONS = ["1.28", "1.29", "1.30", "1.31"]

K8S_PROMPTS = [
    "Deploy a Kubernetes cluster in {region} with {node_count} nodes",
    "Create an EKS cluster, {node_count} nodes, {node_type}",
    "Create an EKS cluster, 3 nodes, m5.large, kubernetes 1.29 in us-east-1",
    "I need a K8s cluster on {cloud_provider}, {region}, medium size",
    "Provision Kubernetes cluster: {cluster_name}, {node_count} nodes",
    "Deploy EKS cluster with {node_count} worker nodes",
    "Create GKE cluster in {region}",
    "Deploy a new Kubernetes cluster",
    "Set up AKS cluster, 3 nodes",
    "Launch EKS cluster in {region}, {node_count} nodes, {node_type}",
    "I want to create a Kubernetes cluster, {node_count} nodes, {region}",
    "Please provision an EKS cluster with {node_count} nodes and {node_type}",
    "Deploy Kubernetes 1.29 cluster in {region} with {node_count} nodes",
]

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
DOCKER_SERVICES = [
    "nginx", "redis", "postgres", "mysql", "mongodb", "rabbitmq", "portainer",
    "grafana", "n8n", "jenkins", "gitea", "elasticsearch", "kafka", "vault",
]
DOCKER_IMAGES = [
    "nginx:latest", "redis:alpine", "postgres:15", "mysql:8", "rabbitmq:3-management",
    "grafana/grafana:latest", "portainer/portainer-ce:latest",
]
PORTS_EXAMPLES = ["80:80", "6379:6379", "5432:5432", "8000:8000", "3000:3000", "8080:8080"]

DOCKER_PROMPTS = [
    "Deploy {docker_service} container on my VM",
    "Run a {docker_service} Docker container",
    "Run a nginx Docker container, port 80:80",
    "I need {docker_service} as a container, port {ports}",
    "Deploy Docker image {docker_image}",
    "Spin up {docker_service} container",
    "Run nginx in Docker",
    "Deploy Redis container",
    "Start a PostgreSQL container with port 5432",
    "Please run a {docker_service} container with ports {ports}",
    "Launch Docker container {docker_image}",
    "I want to run {docker_service} in Docker, port {ports}",
]

# ---------------------------------------------------------------------------
# FastAPI / Static
# ---------------------------------------------------------------------------
APP_PORTS = ["8000", "8080", "3000"]
HTTP_PORTS = ["80", "443", "8080"]

FASTAPI_PROMPTS = [
    "Deploy my FastAPI app to hostname {hostname}",
    "Deploy FastAPI application, app port {app_port}",
    "Deploy FastAPI app billing-api, port 8000, http port 80",
    "I want to deploy a FastAPI app on my VM",
    "Deploy FastAPI to {hostname}, port {app_port}",
    "Please deploy FastAPI app on {hostname}, port {app_port}",
]

STATIC_PROMPTS = [
    "Deploy static website to {hostname}",
    "Deploy static website to nginx on docs.example.com, port 80",
    "Deploy static HTML site to my server",
    "I need to deploy a static website, nginx, port 80",
    "Deploy static website to nginx on {hostname}",
    "Please deploy static site to {hostname} on port 80",
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_ENGINES = ["postgres", "postgresql", "mysql"]
POSTGRES_VERSIONS = ["14", "15", "16"]
DB_PORTS = ["5432", "3306", "27017"]

DB_PROMPTS = [
    "Provision PostgreSQL database on {hostname}",
    "Deploy Postgres database, version {postgres_version}",
    "Deploy PostgreSQL database, version 16, name analytics_db, user admin",
    "I need a PostgreSQL database on my VM",
    "Set up MySQL database",
    "Provision database: {database_engine}, name {database_name}",
    "Deploy Postgres database, version 16",
    "Please provision a {database_engine} database named {database_name}",
    "I want a PostgreSQL database, version {postgres_version}, user {database_user}",
]

# ---------------------------------------------------------------------------
# Intent weights and helpers
# ---------------------------------------------------------------------------
INTENTS = ["provision_vm", "provision_kubernetes", "provision_docker", "provision_fastapi", "provision_static_website", "provision_database"]
SIZE_TO_DEFAULTS = {
    "small": [("t2.micro", 8), ("t3.micro", 20)],
    "medium": [("t2.medium", 30), ("t3.medium", 40)],
    "large": [("t2.xlarge", 100), ("m5.large", 200)],
}

FIELDNAMES = [
    "deployment_id", "prompt", "intent", "username", "workspace",
    "instance_name", "instance_type", "region", "cloud_provider", "os",
    "volume_size_gb", "volume_type", "environment", "size_tier",
    "cluster_name", "node_count", "node_type", "kubernetes_version",
    "docker_image", "docker_service", "container_name", "ports",
    "hostname", "ssh_username", "key_pair_name",
    "app_name", "app_port", "http_port", "https_port", "server_name",
    "database_engine", "database_name", "database_user", "postgres_version", "port",
    "date", "endpoint_url", "payload",
]


def _str(v):
    return "" if v is None else str(v)


def _empty_row(intent: str) -> dict:
    """Base row with all keys empty except intent."""
    row = {k: "" for k in FIELDNAMES if k not in ("deployment_id", "prompt", "intent", "date", "endpoint_url", "payload")}
    row["intent"] = intent
    return row


def generate_vm_row(idx: int, start_date: datetime) -> dict:
    base = _empty_row("provision_vm")
    base["deployment_id"] = f"DEP-{idx:05d}"
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
            volume_type=volume_type, environment=environment,
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
    return base


def generate_k8s_row(idx: int, start_date: datetime) -> dict:
    base = _empty_row("provision_kubernetes")
    base["deployment_id"] = f"DEP-{idx:05d}"
    base["cluster_name"] = f"cluster-{random.randint(1, 999)}"
    base["node_count"] = random.choice([2, 3, 4, 5])
    base["node_type"] = random.choice(K8S_NODE_TYPES)
    base["region"] = random.choice(REGIONS)
    base["cloud_provider"] = random.choice(["aws", "gcp", "azure"])
    base["environment"] = random.choice(ENVIRONMENTS)
    base["kubernetes_version"] = random.choice(K8S_VERSIONS)
    base["username"] = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    base["workspace"] = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    tpl = random.choice(K8S_PROMPTS)
    try:
        base["prompt"] = tpl.format(
            region=base["region"], node_count=base["node_count"], node_type=base["node_type"],
            cloud_provider=base["cloud_provider"], cluster_name=base["cluster_name"],
        )
    except KeyError:
        base["prompt"] = tpl
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    return base


def generate_docker_row(idx: int, start_date: datetime) -> dict:
    base = _empty_row("provision_docker")
    base["deployment_id"] = f"DEP-{idx:05d}"
    use_service = random.random() < 0.6
    if use_service:
        docker_service = random.choice(DOCKER_SERVICES)
        docker_image = ""
        base["container_name"] = f"{docker_service}-{random.randint(1, 99)}"
    else:
        docker_image = random.choice(DOCKER_IMAGES)
        docker_service = docker_image.split("/")[-1].split(":")[0] if "/" in docker_image else docker_image.split(":")[0]
        base["container_name"] = f"{docker_service}-{random.randint(1, 99)}"
    base["ports"] = random.choice(PORTS_EXAMPLES)
    base["username"] = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    base["workspace"] = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    base["hostname"] = f"vm-{random.randint(1, 999)}.example.com" if random.random() < 0.5 else ""
    base["docker_image"] = docker_image or docker_service
    base["docker_service"] = docker_service
    base["ssh_username"] = "ubuntu" if base["hostname"] else ""
    base["key_pair_name"] = f"key-{random.randint(1, 99)}" if base["hostname"] else ""
    tpl = random.choice(DOCKER_PROMPTS)
    try:
        base["prompt"] = tpl.format(docker_service=docker_service, docker_image=base["docker_image"], ports=base["ports"])
    except KeyError:
        base["prompt"] = tpl
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    return base


def generate_fastapi_row(idx: int, start_date: datetime) -> dict:
    base = _empty_row("provision_fastapi")
    base["deployment_id"] = f"DEP-{idx:05d}"
    base["hostname"] = f"app-{random.randint(1, 999)}.example.com"
    base["app_port"] = random.choice(APP_PORTS)
    base["username"] = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    base["workspace"] = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    base["ssh_username"] = "ubuntu"
    base["key_pair_name"] = f"app-{random.randint(1, 99)}"
    base["app_name"] = f"fastapi-app-{random.randint(1, 99)}"
    base["http_port"] = random.choice(HTTP_PORTS)
    tpl = random.choice(FASTAPI_PROMPTS)
    base["prompt"] = tpl.format(hostname=base["hostname"], app_port=base["app_port"])
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    return base


def generate_static_row(idx: int, start_date: datetime) -> dict:
    base = _empty_row("provision_static_website")
    base["deployment_id"] = f"DEP-{idx:05d}"
    base["hostname"] = f"web-{random.randint(1, 999)}.example.com"
    base["server_name"] = f"www.site-{random.randint(1, 99)}.com" if random.random() < 0.5 else ""
    base["username"] = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    base["workspace"] = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    base["ssh_username"] = "ubuntu"
    base["key_pair_name"] = f"web-{random.randint(1, 99)}"
    base["http_port"] = "80"
    base["https_port"] = "443" if random.random() < 0.5 else ""
    tpl = random.choice(STATIC_PROMPTS)
    base["prompt"] = tpl.format(hostname=base["hostname"])
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    return base


def generate_database_row(idx: int, start_date: datetime) -> dict:
    base = _empty_row("provision_database")
    base["deployment_id"] = f"DEP-{idx:05d}"
    base["database_engine"] = random.choice(DATABASE_ENGINES)
    base["database_name"] = f"db_{random.randint(1, 999)}"
    base["database_user"] = f"dbuser{random.randint(1, 99)}"
    base["postgres_version"] = random.choice(POSTGRES_VERSIONS) if base["database_engine"] in ("postgres", "postgresql") else ""
    base["port"] = random.choice(DB_PORTS)
    base["hostname"] = f"db-{random.randint(1, 999)}.example.com"
    base["username"] = f"user{random.randint(1, 500)}" if random.random() < 0.3 else ""
    base["workspace"] = f"ws-{random.randint(100, 999)}" if random.random() < 0.25 else ""
    base["ssh_username"] = "ubuntu"
    base["key_pair_name"] = f"db-{random.randint(1, 99)}"
    tpl = random.choice(DB_PROMPTS)
    try:
        base["prompt"] = tpl.format(
            hostname=base["hostname"], postgres_version=base["postgres_version"],
            database_engine=base["database_engine"], database_name=base["database_name"],
            database_user=base["database_user"],
        )
    except KeyError:
        base["prompt"] = tpl
    base["date"] = (start_date - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    return base


def generate_row(idx: int, start_date: datetime) -> dict:
    intent = random.choices(
        INTENTS,
        weights=[40, 15, 20, 8, 7, 10],
    )[0]
    generators = {
        "provision_vm": generate_vm_row,
        "provision_kubernetes": generate_k8s_row,
        "provision_docker": generate_docker_row,
        "provision_fastapi": generate_fastapi_row,
        "provision_static_website": generate_static_row,
        "provision_database": generate_database_row,
    }
    return generators[intent](idx, start_date)


def get_endpoint_and_payload(intent: str, row: dict) -> tuple:
    base_provisioner = "http://localhost:8743"
    if intent == "provision_vm":
        url = f"{base_provisioner}/api/v2/tenant/provision/vm"
        payload = {
            "username": row.get("username") or "user",
            "instance_name": row.get("instance_name") or "vm-1",
            "instance_type": row.get("instance_type") or "t3.micro",
            "region": row.get("region") or "us-east-1",
            "cloud_provider": row.get("cloud_provider") or "aws",
            "os": row.get("os") or "ubuntu",
            "volume_size_gb": int(row.get("volume_size_gb") or 30),
            "environment": row.get("environment") or "dev",
        }
        return (url, json.dumps(payload, indent=0))
    if intent == "provision_kubernetes":
        url = f"{base_provisioner}/api/v2/tenant/provision/kubernetescluster/deploy"
        payload = {
            "username": row.get("username") or "user",
            "cluster_name": row.get("cluster_name") or "cluster-1",
            "node_count": int(row.get("node_count") or 2),
            "node_type": row.get("node_type") or "t3.medium",
            "region": row.get("region") or "us-east-1",
            "cloud_provider": row.get("cloud_provider") or "aws",
            "kubernetes_version": row.get("kubernetes_version") or "1.28",
        }
        return (url, json.dumps(payload, indent=0))
    if intent == "provision_database":
        url = f"{base_provisioner}/api/v2/tenant/provision/databases"
        payload = {
            "username": row.get("username") or "user",
            "engine": row.get("database_engine") or "postgres",
            "database_name": row.get("database_name") or "appdb",
            "region": row.get("region") or "us-east-1",
            "cloud_provider": row.get("cloud_provider") or "aws",
        }
        return (url, json.dumps(payload, indent=0))
    if intent == "provision_docker":
        url = f"{base_provisioner}/api/v2/tenant/provision/docker"
        payload = {
            "username": row.get("username") or "user",
            "hostname": row.get("hostname") or "",
            "ssh_username": row.get("ssh_username") or "ubuntu",
            "docker_image": row.get("docker_image") or "nginx",
            "container_name": row.get("container_name") or "app",
            "ports": row.get("ports") or "80:80",
        }
        return (url, json.dumps(payload, indent=0))
    if intent == "provision_static_website":
        url = f"{base_provisioner}/api/v1/infrastructure/services/staticwebsite/deploy"
        payload = {
            "hostname": row.get("hostname") or row.get("server_name") or "web-1.example.com",
            "http_port": row.get("http_port") or "80",
            "server_name": row.get("server_name") or "www.site.com",
        }
        return (url, json.dumps(payload, indent=0))
    if intent == "provision_fastapi":
        url = f"{base_provisioner}/api/v1/infrastructure/services/fastapi/deploy"
        payload = {
            "hostname": row.get("hostname") or row.get("server_name") or "app-1.example.com",
            "app_port": row.get("app_port") or "8000",
            "http_port": row.get("http_port") or "8080",
        }
        return (url, json.dumps(payload, indent=0))
    return (f"{base_provisioner}/api/v2/workflow/execute", json.dumps({"metadata": {"name": "provision"}}, indent=0))


def main():
    parser = argparse.ArgumentParser(description="Prepare cloud_deployments.csv for provisioning training (5000 rows)")
    parser.add_argument("--rows", type=int, default=5000, help="Number of rows (default 5000)")
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "app" / "data" / "datasets" / "cloud_deployments.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start_date = datetime.now()

    rows = []
    for i in range(args.rows):
        row = generate_row(i, start_date)
        intent = row["intent"]
        endpoint_url, payload_str = get_endpoint_and_payload(intent, row)
        row["endpoint_url"] = endpoint_url
        row["payload"] = payload_str.replace("\n", " ").replace('"', "'")[:2000]
        out = {k: _str(row.get(k, "")) for k in FIELDNAMES}
        rows.append(out)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    intent_counts = {}
    for r in rows:
        intent_counts[r["intent"]] = intent_counts.get(r["intent"], 0) + 1
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")


if __name__ == "__main__":
    main()
