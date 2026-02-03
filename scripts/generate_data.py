
import argparse
import json
import random
import uuid
from typing import List, Dict, Any
from pathlib import Path

# Intents mirroring InfinityAI/agent.py
INTENTS = [
    "provision_vm",
    "provision_network",
    "provision_storage",
    "provision_kubernetes"
]

# Sample data
OS_TYPES = ["ubuntu", "ubuntu 22.04", "ubuntu 24.04", "windows", "centos", "rhel"]
INSTANCE_TYPES = ["t2.micro", "t2.medium", "t2.large", "t3.medium", "m5.large"]
REGIONS = ["us-east-1", "us-west-2", "eu-central-1", "ap-southeast-1"]
PROVIDERS = ["aws", "azure", "gcp"]
STORAGE_TYPES = ["s3", "ebs", "blob", "gcs"]

def generate_vm_sample() -> Dict[str, Any]:
    """Generate a VM provisioning sample"""
    # Randomly select parameters
    os_type = random.choice(OS_TYPES)
    instance_type = random.choice(INSTANCE_TYPES)
    region = random.choice(REGIONS)
    provider = random.choice(PROVIDERS)
    name = f"web-server-{random.randint(100, 999)}"
    
    # Construct Natural Language Query
    templates = [
        f"Provision a {instance_type} VM with {os_type} in {region}",
        f"Create a new virtual machine named {name}",
        f"Spin up a {instance_type} instance on {provider}",
        f"I need a server with {os_type} in {region}",
        f"Deploy a {instance_type} node"
    ]
    query = random.choice(templates)
    
    # Construct "Ground Truth" Payload (what we want the model to output)
    payload = {
        "intent": "provision_vm",
        "parameters": {
            "instance_type": instance_type,
            "os": os_type if "ubuntu" in os_type or "windows" in os_type or "centos" in os_type else None,
            "region": region,
            "cloud_provider": provider if provider in query else None,
            "instance_name": name if name in query else None
        }
    }
    
    # Clean up None values to mimic minimal valid payload
    payload["parameters"] = {k: v for k, v in payload["parameters"].items() if v is not None}
    
    return {
        "query": query,
        "output": json.dumps(payload, indent=2)
    }

def generate_storage_sample() -> Dict[str, Any]:
    """Generate a Storage provisioning sample"""
    storage_type = random.choice(STORAGE_TYPES)
    bucket_name = f"my-data-{random.randint(1000, 9999)}"
    
    templates = [
        f"Create an {storage_type} bucket named {bucket_name}",
        f"I need storage for my app, specifically {storage_type}",
        f"Provision a storage volume",
        f"Make a new {storage_type} container"
    ]
    
    query = random.choice(templates)
    
    payload = {
        "intent": "provision_storage",
        "parameters": {
            "storage_type": storage_type,
            "resource_name": bucket_name if bucket_name in query else None
        }
    }
    payload["parameters"] = {k: v for k, v in payload["parameters"].items() if v is not None}
    
    return {
        "query": query,
        "output": json.dumps(payload, indent=2)
    }

def generate_k8s_sample() -> Dict[str, Any]:
    """Generate a Kubernetes provisioning sample"""
    node_count = random.choice([2, 3, 5, 10])
    cluster_name = f"k8s-cluster-{random.randint(1, 99)}"
    
    templates = [
        f"Deploy a kubernetes cluster with {node_count} nodes",
        f"Create a k8s cluster named {cluster_name}",
        f"I need a fresh kubernetes environment",
        f"Spin up an EKS cluster with {node_count} worker nodes"
    ]
    
    query = random.choice(templates)
    
    payload = {
        "intent": "provision_kubernetes",
        "parameters": {
            "node_count": node_count if str(node_count) in query else 3,
            "cluster_name": cluster_name if cluster_name in query else None
        }
    }
    payload["parameters"] = {k: v for k, v in payload["parameters"].items() if v is not None}
    
    return {
        "query": query,
        "output": json.dumps(payload, indent=2)
    }

def generate_dataset(size: int = 100, output_file: str = "training_data.json"):
    """Generate a full dataset"""
    data = []
    
    generators = [generate_vm_sample, generate_storage_sample, generate_k8s_sample]
    
    for _ in range(size):
        gen = random.choice(generators)
        data.append(gen())
        
    # Save to file
    output_path = Path(__file__).parent / "data" / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"✅ Generated {size} samples in {output_path}")
    return output_path


def main(argv: List[str] | None = None):
    parser = argparse.ArgumentParser(description="VaLLM data generation")
    parser.add_argument(
        "--mode",
        choices=["json", "create-base", "expand", "full"],
        default="full",
        help="Mode: json (nlu), create-base (reset csvs), expand (grow csvs), full (reset+grow)",
    )
    parser.add_argument("--size", type=int, default=100, help="Number of JSON samples (mode=json)")
    parser.add_argument(
        "--output-file",
        default="training_data.json",
        help="Output JSON filename under app/data/ (mode=json)",
    )
    parser.add_argument(
        "--target-rows",
        type=int,
        default=1000,
        help="Target rows per CSV file (mode=expand/full)",
    )

    args = parser.parse_args(argv)

    if args.mode == "json":
        generate_dataset(size=args.size, output_file=args.output_file)
        return 0

    # Import here to avoid circular imports or heavyweight loads if just doing JSON
    try:
        from .massive_data_expansion import create_base_datasets, expand_all_datasets
    except ImportError:
        from massive_data_expansion import create_base_datasets, expand_all_datasets

    if args.mode == "create-base":
        create_base_datasets()
        return 0

    if args.mode == "expand":
        expand_all_datasets(target_rows=args.target_rows)
        return 0

    if args.mode == "full":
        create_base_datasets()
        expand_all_datasets(target_rows=args.target_rows)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
