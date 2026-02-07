# VaLLM User Manual

## Multi-Cloud LLM Platform for Intent-Driven Infrastructure Provisioning

**Version:** 1.0.0
**Project:** VaLLM (Vector-based Local LLM)
**Purpose:** Reinforcement Learning Reference & Operator Guide

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Dataset Provisioning & Formats](#3-dataset-provisioning--formats)
4. [Intent Classification System](#4-intent-classification-system)
5. [Cloud Provisioning Pipeline](#5-cloud-provisioning-pipeline)
6. [Model Training & Fine-Tuning](#6-model-training--fine-tuning)
7. [Embedding & Vector Search](#7-embedding--vector-search)
8. [Reasoning Engine](#8-reasoning-engine)
9. [API Reference](#9-api-reference)
10. [Multi-Provider LLM Support](#10-multi-provider-llm-support)
11. [Reinforcement Learning with Human Feedback (RLHF)](#11-reinforcement-learning-with-human-feedback-rlhf)
12. [Service Integrations](#12-service-integrations)
13. [Monitoring & Observability](#13-monitoring--observability)
14. [Deployment Guide](#14-deployment-guide)
15. [Dataset Schema Reference](#15-dataset-schema-reference)
16. [Appendix: Intent-to-Response Mapping Table](#16-appendix-intent-to-response-mapping-table)

---

## 1. Executive Summary

VaLLM is a **production-grade, multi-cloud LLM platform** that translates natural language user queries into cloud infrastructure provisioning actions. The system combines:

- **Semantic vector search** (FAISS + sentence-transformers) for intent matching
- **Multi-model LLM orchestration** (OpenAI, Anthropic, Gemini, Qwen, DeepSeek, Ollama, HuggingFace)
- **Chain-of-thought reasoning** for complex decision-making
- **Human-in-the-loop feedback** (RLHF) for continuous model improvement
- **Multi-cloud provisioning** (AWS, Azure, GCP) with Golang backend integration

### Core Workflow

```
User Query (Natural Language)
    |
    v
[Intent Detection] --> Vector search against training datasets
    |
    v
[Confidence Scoring] --> Cosine similarity threshold (>0.2)
    |
    v
[Payload Generation] --> Golang-ready JSON for cloud provisioning
    |
    v
[Agent Validation] --> InfinityAI cloud agent reviews payload
    |
    v
[Infrastructure Provisioning] --> Golang backend provisions resources
    |
    v
[User Feedback] --> Thumbs up/down for RLHF training loop
```

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-------------------------------------------------------------------+
|                       VaLLM Application                            |
|                    FastAPI Server (Port 8000)                       |
+-------------------------------------------------------------------+
|                                                                     |
|  +-------------------+  +-------------------+  +-----------------+ |
|  | Vector Store      |  | Reasoning Engine  |  | Cloud Intent    | |
|  | (FAISS)           |  | (Chain-of-Thought)|  | Classifier      | |
|  | 384-dim embeddings|  | Multi-step        |  | 6 provisioning  | |
|  | Cosine similarity |  | Intent+Context    |  | + 5 query types | |
|  +-------------------+  +-------------------+  +-----------------+ |
|                                                                     |
|  +-------------------+  +-------------------+  +-----------------+ |
|  | Model Registry    |  | Eval/Feedback     |  | Request Logger  | |
|  | Multi-provider    |  | RLHF pipeline     |  | Training data   | |
|  | Draft/Prod/Archive|  | Thumbs up/down    |  | JSONL export    | |
|  +-------------------+  +-------------------+  +-----------------+ |
|                                                                     |
+-------------------------------------------------------------------+
|  Supporting Services                                                |
|  +--------+ +----------+ +-------+ +--------+ +-----------------+ |
|  | Redis  | | RabbitMQ | | Kafka | | Celery | | PostgreSQL      | |
|  | Cache  | | Queue    | | Events| | Tasks  | | Persistence     | |
|  +--------+ +----------+ +-------+ +--------+ +-----------------+ |
+-------------------------------------------------------------------+
```

### 2.2 Component Responsibilities

| Component | Purpose | Technology |
|-----------|---------|------------|
| **FastAPI App** | HTTP API server, routing, middleware | FastAPI + Uvicorn |
| **Vector Store** | Semantic search over datasets | FAISS + sentence-transformers |
| **Reasoning Engine** | Chain-of-thought intent analysis | Custom Python engine |
| **Cloud Intent API** | Provisioning payload generation | FastAPI router |
| **Model Registry** | LLM model lifecycle management | SQLAlchemy + PostgreSQL |
| **Eval Service** | Human feedback collection | FastAPI + PostgreSQL |
| **Request Logger** | Training data capture | PostgreSQL + JSONL export |
| **Redis** | Caching, rate limiting, Celery broker | Redis 7 |
| **Kafka** | Cloud infrastructure event streaming | Kafka with idempotent writes |
| **RabbitMQ** | Task messaging (AMQP) | RabbitMQ with Pika |
| **Celery** | Distributed task execution | Celery 5 + Redis |
| **PostgreSQL** | Persistent storage, audit trails | PostgreSQL 14-16 |
| **Prometheus** | Metrics collection | Prometheus + Grafana |

### 2.3 Directory Structure

```
va_llm_v1/
|-- app/
|   |-- __init__.py                    # App initialization (v1.0.0)
|   |-- core/
|   |   |-- settings.py                # Enterprise configuration management
|   |   |-- cors.py                    # CORS middleware configuration
|   |   |-- logger.py                  # Lambda-compatible logging
|   |   |-- logging_config.py          # JSON structured logging
|   |   |-- celery_app.py              # Celery task queue config
|   |   |-- model_loader.py            # Model loading utilities
|   |   |-- model_manager.py           # Multi-provider model orchestration
|   |   |-- model_registry.py          # Model registry with capabilities
|   |-- auth/
|   |   |-- rate_limit.py              # In-memory rate limiter
|   |-- services/
|   |   |-- ai/
|   |   |   |-- ml/
|   |   |   |   |-- routes.py          # V1/V2/V3 ML API endpoints
|   |   |   |   |-- cloud_routes.py    # Cloud provisioning intent API
|   |   |   |   |-- reasoning.py       # Chain-of-thought reasoning engine
|   |   |   |   |-- embeddings.py      # FAISS vector store + embeddings
|   |   |   |   |-- train.py           # Model fine-tuning pipeline
|   |   |   |   |-- precompute.py      # Offline FAISS index builder
|   |   |   |   |-- cache.py           # ML result caching
|   |   |   |   |-- circuit_breaker.py # Fault tolerance
|   |   |   |   |-- exceptions.py      # Custom ML exceptions
|   |   |   |-- agents/                # AI agent integrations
|   |   |-- platform/
|   |   |   |-- database.py            # PostgreSQL connection management
|   |   |   |-- models.py              # SQLAlchemy ORM models
|   |   |   |-- model_router.py        # Model CRUD API
|   |   |   |-- model_service.py       # Model business logic
|   |   |   |-- eval_router.py         # Feedback/evaluation API
|   |   |   |-- eval_service.py        # Evaluation business logic
|   |   |   |-- health_probe_router.py # Health checks
|   |   |   |-- lifecycle_hooks.py     # Background cleanup tasks
|   |   |   |-- request_logger.py      # Request logging for RLHF
|   |   |   |-- tenant_rate_limit.py   # Redis-based tenant rate limits
|   |   |-- redis/                     # Redis service + routes
|   |   |-- rabbitmq/                  # RabbitMQ service + routes
|   |   |-- kafka/                     # Kafka cloud events + routes
|   |   |-- celery/                    # Celery task service + routes
|   |   |-- monitoring/                # Full monitoring suite
|   |-- data/
|   |   |-- datasets/                  # Training datasets (CSV, JSON, TXT)
|   |   |-- vectorstore/               # FAISS index + document pickles
|   |   |-- model/                     # Fine-tuned model artifacts
|   |-- tests/
|       |-- tests.py                   # Integration tests
|-- scripts/
|   |-- data_pipeline/
|   |   |-- s3_fetcher.py              # Download from AWS S3
|   |   |-- azure_blob_fetcher.py      # Download from Azure Blob Storage
|   |   |-- url_fetcher.py             # Download from HTTP/HTTPS URLs
|   |   |-- process_datasets.py        # Deduplication, validation, cleaning
|   |-- generate_cloud_deployments.py  # Generate synthetic training data
|   |-- generate_data.py               # General data generation
|-- deployment/
|   |-- kubernetes/
|   |   |-- eks/                       # AWS EKS manifests
|   |   |-- aks/                       # Azure AKS manifests
|   |   |-- deployment.yaml            # Generic K8s deployment
|   |   |-- service.yaml               # K8s service definition
|   |-- monitoring/
|       |-- prometheus.yml             # Prometheus configuration
|-- .github/workflows/                 # GitHub Actions CI/CD
|-- .gitlab-ci.yml                     # GitLab CI/CD
|-- azure-pipelines.yml                # Azure DevOps CI/CD
|-- Dockerfile                         # Container build definition
|-- docker-compose.yml                 # Local development stack
|-- requirements.txt                   # Python dependencies
```

---

## 3. Dataset Provisioning & Formats

### 3.1 Dataset Sources

VaLLM supports ingesting training data from multiple sources:

| Source | Fetcher Script | Schedule (K8s) |
|--------|---------------|-----------------|
| **AWS S3** | `scripts/data_pipeline/s3_fetcher.py` | Daily at 2 AM UTC |
| **Azure Blob Storage** | `scripts/data_pipeline/azure_blob_fetcher.py` | Daily at 2 AM UTC |
| **HTTP/HTTPS URLs** | `scripts/data_pipeline/url_fetcher.py` | Every 6 hours |
| **Local Filesystem** | Direct file placement in `app/data/datasets/` | N/A |

### 3.2 S3 Dataset Fetcher

```bash
python scripts/data_pipeline/s3_fetcher.py \
    --bucket my-training-data \
    --prefix datasets/ \
    --destination app/data/datasets \
    --max-size 50GB \
    --region us-east-1
```

**Features:**
- SHA-256 checksum verification after download
- Size limit enforcement (skip files exceeding max-size)
- Automatic directory creation
- Progress logging with success/failure tracking

### 3.3 Azure Blob Storage Fetcher

```bash
python scripts/data_pipeline/azure_blob_fetcher.py \
    --account mystorageaccount \
    --container datasets \
    --prefix training/ \
    --destination app/data/datasets \
    --max-size 50GB
```

**Authentication:** Azure Managed Identity or connection string

### 3.4 URL Dataset Fetcher

```bash
python scripts/data_pipeline/url_fetcher.py \
    --urls-file config/dataset_urls.txt \
    --destination app/data/datasets \
    --max-size 50GB \
    --verify-ssl
```

**URL File Format:**
```
# One URL per line
# Format: URL|DESTINATION_FILENAME|CHECKSUM (optional)
https://example.com/datasets/incidents.csv|incidents.csv|sha256:abc123
https://example.com/datasets/resources.csv|resources.csv
```

### 3.5 Dataset Processing Pipeline

```bash
python scripts/data_pipeline/process_datasets.py \
    --source app/data/datasets \
    --output app/data/processed \
    --format csv \
    --validate \
    --deduplicate
```

**Processing Steps:**
1. **CSV Parsing** - Read all CSV files with automatic encoding detection
2. **Row Deduplication** - MD5 hashing of row content to remove exact duplicates
3. **Validation** - Check for required fields, data types, value ranges
4. **Metadata Generation** - Creates `processing_metadata.json` with statistics
5. **Output** - Clean, deduplicated datasets ready for training

### 3.6 Synthetic Training Data Generation

```bash
python scripts/generate_cloud_deployments.py \
    --output app/data/datasets/cloud_deployments.csv \
    --rows 2500
```

**Generation Weights (default 2500 rows):**

| Intent Type | Weight | Approx. Rows |
|------------|--------|--------------|
| `provision_vm` | 40% | 1000 |
| `provision_docker` | 20% | 500 |
| `provision_kubernetes` | 15% | 375 |
| `provision_database` | 10% | 250 |
| `provision_fastapi` | 8% | 200 |
| `provision_static_website` | 7% | 175 |

### 3.7 Dataset Files

#### 3.7.1 `cloud_deployments.csv` (Primary Training Dataset)

**Schema:**

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| deployment_id | string | dep-001 | Unique deployment identifier |
| prompt | string | "Deploy a t2.micro EC2 instance in us-east-1" | Natural language user query |
| intent | string | provision_vm | Classified intent label |
| username | string | john_doe | Target workspace user |
| workspace | string | prod-workspace | Target workspace |
| instance_name | string | web-server-01 | VM instance name |
| instance_type | string | t2.micro, t3.medium, m5.large | Cloud instance type |
| region | string | us-east-1, eu-west-1 | Cloud region |
| cloud_provider | string | aws, azure, gcp | Cloud provider |
| os | string | ubuntu, centos, windows | Operating system |
| volume_size_gb | int | 30 | Storage volume size |
| volume_type | string | gp2, gp3 | Storage volume type |
| environment | string | dev, staging, prod | Target environment |
| cluster_name | string | prod-cluster | K8s cluster name |
| node_count | int | 2-5 | K8s node count |
| node_type | string | t3.medium, m5.large | K8s node type |
| kubernetes_version | string | 1.28, 1.29, 1.30 | K8s version |
| docker_image | string | nginx:latest | Docker image |
| container_name | string | web-nginx | Docker container name |
| ports | string | 80:80, 8000:8000 | Port mapping |
| database_engine | string | postgresql, mysql, mongodb | Database engine |
| database_name | string | mydb | Database name |
| database_user | string | admin | Database user |
| app_name | string | my-api | FastAPI app name |
| app_port | int | 8000 | Application port |

#### 3.7.2 `cloud_observability.csv` (Incident Dataset)

**Schema:**

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| id | string | INC-001 | Incident identifier |
| record_type | string | incident, metric, alert | Record type |
| category | string | availability, performance, security | Category |
| severity_or_priority | string | critical, high, medium, low | Severity level |
| service | string | api-gateway, database, kubernetes | Affected service |
| error_code | string | 500, 503, OOM, TIMEOUT | Error code |
| description | string | "Database connection pool exhausted" | Human-readable description |
| root_cause | string | "Max connections exceeded" | Root cause analysis |
| resolution_or_recommendation | string | "Implement PgBouncer" | Resolution steps |
| prevention_or_impact | string | "Set connection pool limits" | Prevention measures |
| tags | string | "database,connection,pool" | Searchable tags |
| timestamp | datetime | 2024-01-15T10:30:00Z | Event timestamp |

#### 3.7.3 `deployments.json` (Deployment Use Cases)

**Structure:**
```json
{
  "use_cases": [
    {
      "id": "uc-001",
      "category": "vm_provisioning",
      "prompt": "Create an EC2 instance with t3.medium in us-west-2",
      "intent": "provision_vm",
      "api_endpoint": "/api/v2/tenant/provision/vm",
      "payload": {
        "instance_type": "t3.medium",
        "region": "us-west-2",
        "cloud_provider": "aws"
      },
      "expected_response": "VM provisioning initiated..."
    }
  ]
}
```

#### 3.7.4 Knowledge Base Text Files

**`cloud_operations_provisionning_knowledge1.txt`** and **`knowledge2.txt`**

These files contain unstructured knowledge about:
- Intent-to-Decision Mapping Framework
- Business requirement classification
- Infrastructure decision logic per use case
- Compliance and security requirements (HIPAA, SOC 2, PCI-DSS)
- Cost optimization strategies

**Example Entry:**
```
Intent: High-Availability Production
Business Requirements: Zero downtime SLA, SOC 2 compliance
AI Agent Decision:
  - Multi-AZ EKS cluster
  - Multi-AZ RDS with read replicas
  - WAF + Shield for DDoS protection
  - IAM least privilege policies
  - KMS encryption for data at rest
```

---

## 4. Intent Classification System

### 4.1 Overview

The intent classification system operates at two levels:

1. **Vector-based classification** (primary) - Semantic similarity search against the training dataset
2. **Keyword-based classification** (fallback) - Rule-based keyword matching when vector search confidence is low

### 4.2 Supported Intents

#### Provisioning Intents (query_type: "provisioning")

| Intent | Trigger Keywords | Target API |
|--------|-----------------|------------|
| `provision_vm` | provision, create, deploy, setup, launch, spin up + VM/instance/EC2 | POST /api/v2/tenant/provision/vm |
| `provision_kubernetes` | provision + kubernetes/k8s/cluster/EKS/AKS/GKE | POST /api/v2/tenant/provision/kubernetescluster/deploy |
| `provision_docker` | provision + docker/container/image | POST /api/v2/tenant/provision/docker |
| `provision_database` | provision + database/RDS/PostgreSQL/MySQL/MongoDB | POST /api/v2/tenant/provision/database |
| `provision_fastapi` | provision + fastapi/api/application | POST /api/v2/tenant/provision/fastapi |
| `provision_static_website` | provision + website/static/nginx/hosting | POST /api/v2/tenant/provision/static-website |

#### Non-Provisioning Intents (query_type varies)

| Query Type | Trigger Keywords | System Response |
|-----------|-----------------|-----------------|
| `incident` | error, outage, failure, crash, incident, down | Search incident KB, provide resolution |
| `cost` | cost, spend, budget, expensive, pricing | Cost analysis and optimization advice |
| `billing` | billing, invoice, payment, charge | Billing information and clarification |
| `security` | security, encrypt, vulnerability, breach, compliance | Security assessment and recommendations |
| `recommendation` | recommend, suggest, best practice, optimize | Best practice recommendations |
| `other` | (none of the above) | General cloud operations assistance |

### 4.3 Intent Detection Flow

```
User Query: "Spin up a Kubernetes cluster with 3 nodes in AWS"
    |
    v
Step 1: Vector Search
    - Encode query using sentence-transformers (384-dim)
    - Search FAISS index for top-K similar training prompts
    - Filter results by content_type = "deployment"
    |
    v
Step 2: Confidence Check
    - Best match score > 0.2? (cosine similarity)
    |
    +-- YES --> Extract intent from CSV metadata
    |           intent = "provision_kubernetes"
    |           raw = {cluster_name, node_count, ...}
    |
    +-- NO  --> Fallback to keyword classification
                Scan for: incident, cost, billing, security, recommendation
                Return query_type without provisioning payload
    |
    v
Step 3: Payload Generation
    - Map CSV row fields to Golang-ready JSON payload
    - Apply defaults for missing fields
    - Return {query_type, intent, payload, confidence, match_prompt}
```

### 4.4 Confidence Scoring

- **Metric:** Cosine similarity (FAISS IndexFlatIP with L2 normalization)
- **Dimension:** 384 (sentence-transformers/all-MiniLM-L6-v2)
- **Threshold:** 0.2 (tunable)
- **Interpretation:**
  - `> 0.8` = High confidence, exact match
  - `0.5 - 0.8` = Good match, may need agent review
  - `0.2 - 0.5` = Low confidence, agent should validate
  - `< 0.2` = No match, classify as non-provisioning

---

## 5. Cloud Provisioning Pipeline

### 5.1 End-to-End Flow

```
+------------------+     +------------------+     +------------------+
| User Query       | --> | VaLLM Intent API | --> | Agent Validation |
| (Natural Lang.)  |     | /provision-intent|     | (InfinityAI)     |
+------------------+     +------------------+     +------------------+
                                                         |
                                                         v
                          +------------------+     +------------------+
                          | Infrastructure   | <-- | Golang Backend   |
                          | (AWS/Azure/GCP)  |     | Provisioner API  |
                          +------------------+     +------------------+
```

### 5.2 Payload Schemas by Intent

#### provision_vm

```json
{
  "username": "john_doe",
  "workspace": "prod-workspace",
  "workspace_id": "prod-workspace",
  "user_id": "john_doe",
  "instance_name": "web-server-01",
  "resource_name": "web-server-01",
  "instance_type": "t3.medium",
  "region": "us-east-1",
  "cloud_provider": "aws",
  "os": "ubuntu",
  "volume_size": 30,
  "volume_type": "gp3",
  "environment": "production",
  "hostname": "web-server-01.example.com",
  "ssh_username": "ubuntu",
  "key_pair_name": "prod-key"
}
```

#### provision_kubernetes

```json
{
  "username": "john_doe",
  "workspace": "prod-workspace",
  "cluster_name": "prod-cluster",
  "node_count": 3,
  "node_type": "t3.large",
  "kubernetes_version": "1.29",
  "region": "us-east-1",
  "cloud_provider": "aws"
}
```

#### provision_docker

```json
{
  "username": "john_doe",
  "workspace": "prod-workspace",
  "docker_image": "nginx:latest",
  "image": "nginx:latest",
  "container_name": "web-nginx",
  "docker_service": "nginx",
  "ports": "80:80"
}
```

#### provision_database

```json
{
  "username": "john_doe",
  "workspace": "prod-workspace",
  "hostname": "db-server.example.com",
  "database_engine": "postgresql",
  "database_name": "mydb",
  "database_user": "admin",
  "postgres_version": "16",
  "port": 5432,
  "ssh_username": "ubuntu",
  "key_pair_name": "db-key"
}
```

#### provision_fastapi

```json
{
  "username": "john_doe",
  "workspace": "prod-workspace",
  "hostname": "api.example.com",
  "app_name": "my-api",
  "app_port": 8000,
  "http_port": 8080,
  "ssh_username": "ubuntu",
  "key_pair_name": "api-key"
}
```

#### provision_static_website

```json
{
  "username": "john_doe",
  "workspace": "prod-workspace",
  "hostname": "www.example.com",
  "server_name": "www.example.com",
  "http_port": 80,
  "ssh_username": "ubuntu",
  "key_pair_name": "web-key"
}
```

### 5.3 Cloud Provider Support Matrix

| Feature | AWS | Azure | GCP |
|---------|-----|-------|-----|
| VM Provisioning | EC2 | Azure VMs | Compute Engine |
| Kubernetes | EKS | AKS | GKE |
| Database | RDS | Azure SQL | Cloud SQL |
| Container Registry | ECR | ACR | GCR |
| Object Storage | S3 | Blob Storage | GCS |
| Load Balancer | NLB/ALB | Azure LB | Cloud LB |
| Monitoring | CloudWatch | Azure Monitor | Cloud Monitoring |

### 5.4 Intent-to-Infrastructure Decision Framework

The knowledge base files provide decision logic for translating business intents into infrastructure:

| User Intent | Business Requirements | Infrastructure Decision |
|------------|----------------------|------------------------|
| High-Availability Production | Zero downtime, SOC 2 | Multi-AZ EKS, Multi-AZ RDS, WAF+Shield, KMS |
| Cost-Optimized Development | Budget <$200/mo | Single-AZ, t3/t4g burstable, auto-shutdown |
| Data Processing Pipeline | High throughput, batch | Spot instances, S3 lifecycle, VPC endpoints |
| Regulated Workload (HIPAA) | PHI handling, encryption | Dedicated VPC, PrivateLink, CloudTrail, KMS |
| E-Commerce Platform | PCI-DSS, 99.99% uptime | Multi-region, ElastiCache, Aurora Global DB |
| ML Training | GPU workloads | P4d/P5 Spot, FSx for Lustre, SageMaker |
| Real-Time Analytics | Sub-second latency | Kinesis, OpenSearch, Lambda, WebSocket |
| Disaster Recovery | RPO<15min, RTO<1hr | Pilot light, cross-region RDS, S3 CRR |

---

## 6. Model Training & Fine-Tuning

### 6.1 Training Pipeline Overview

```
Datasets (CSV/JSON/TXT/PDF)
    |
    v
[Multi-Format Data Loading]
    |
    v
[Text Conversion] --> Each row/record becomes a training text
    |
    v
[Tokenization] --> HuggingFace tokenizer (max 512 tokens)
    |
    v
[Fine-Tuning] --> Causal LM training (distilgpt2 / Qwen2.5)
    |
    v
[Model Artifacts] --> config.json, tokenizer.json, pytorch_model.bin
    |
    v
[Saved to] --> app/data/model/
```

### 6.2 Supported Base Models

| Model | Parameters | Use Case | Hardware |
|-------|-----------|----------|----------|
| sentence-transformers/all-MiniLM-L6-v2 | 22M | Embeddings (384-dim) | CPU |
| distilgpt2 | 82M | Causal LM, CPU-friendly | CPU |
| microsoft/phi-2 | 2.7B | Advanced reasoning | GPU recommended |
| Qwen/Qwen2.5-3B | 3B | Multilingual | GPU recommended |
| Qwen/Qwen2.5-7B | 7B | High quality | GPU required |

### 6.3 Training Configuration

```python
Training Parameters:
    batch_size_per_device: 4
    gradient_accumulation_steps: 4
    num_train_epochs: 1-3
    learning_rate: 5e-5
    max_seq_length: 512
    precision: bf16 (GPU) / fp32 (CPU)
    warmup_ratio: 0.1
    weight_decay: 0.01
    save_strategy: "epoch"
```

### 6.4 Text Conversion Templates

**CSV Row Conversion:**
```
"You are an AI assistant for cloud observability. Analyze the following
telemetry record and provide insights.

[field1]: [value1] | [field2]: [value2] | ... | [fieldN]: [valueN]

Answer:"
```

**JSON Record Conversion (with category):**
```
"Analyze the following [category] data and provide insights on
performance and optimization:

[flattened key-value pairs]

Answer:"
```

**TXT Conversion:**
- Chunked by section headers or paragraph boundaries
- Each chunk becomes an independent training sample

### 6.5 Running Training

```bash
# Basic training with default model (distilgpt2)
python -m app.services.ai.ml.train

# Training with specific model
python -m app.services.ai.ml.train --model_name "Qwen/Qwen2.5-3B"

# Training with custom dataset directory
python -m app.services.ai.ml.train --data_dir app/data/datasets
```

---

## 7. Embedding & Vector Search

### 7.1 Embedding Model

- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Index Type:** FAISS IndexFlatIP (Inner Product with L2 normalization = Cosine similarity)
- **Storage:** `app/data/vectorstore/faiss_index.bin` + `documents.pkl`

### 7.2 Vector Store Operations

**Storing Embeddings:**
```python
async def store_embeddings(
    texts: List[str],           # Documents to embed
    content_type: str,          # "deployment", "incident", etc.
    content_ids: List[str],     # Unique identifiers
    metadata_list: List[Dict]   # Raw CSV/JSON data per document
):
    embeddings = model.encode(texts, convert_to_numpy=True)  # (N, 384)
    faiss.normalize_L2(embeddings)
    faiss_index.add(embeddings)
    # Store document + metadata for retrieval
```

**Searching:**
```python
async def search(
    query: str,
    top_k: int = 5,
    filter_type: Optional[str] = None  # "deployment", "incident"
) -> List[Dict]:
    query_embedding = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)
    distances, indices = faiss_index.search(query_embedding, top_k)
    # Return ranked results with scores and metadata
```

### 7.3 Precomputing the Index

```bash
# Build FAISS index from all datasets
python -m app.services.ai.ml.precompute

# Steps:
# 1. Discover all CSVs in app/data/datasets/
# 2. Convert rows to text documents
# 3. Generate embeddings in batches (batch_size=128)
# 4. Build FAISS index
# 5. Save index + metadata
```

### 7.4 Caching Strategy

| Cache Type | Key | TTL | Purpose |
|-----------|-----|-----|---------|
| Embedding Cache | normalized(query) | Session | Avoid re-encoding same queries |
| Search Cache | (query, top_k, filter_type) | Session | Avoid re-searching same queries |

Both caches are thread-safe with `RLock`.

---

## 8. Reasoning Engine

### 8.1 Chain-of-Thought Pipeline

The reasoning engine performs multi-step analysis for complex queries:

```
Step 1: INTENT DETECTION
    - Keyword scoring against intent_keywords dictionary
    - Returns: {intent, confidence, metadata}

Step 2: CONTEXT GATHERING
    - Vector search for top-10 related documents
    - Returns: List of relevant context documents

Step 3: ANALYSIS
    - Extract resource types, regions, problems from context
    - Pattern matching across incident records
    - Returns: Analysis summary

Step 4: SYNTHESIS
    - Combine findings with intent-specific insights
    - Cross-reference with knowledge base
    - Returns: Synthesized recommendations

Step 5: DECISION
    - Generate actionable response
    - Include confidence score
    - Returns: Final answer with reasoning chain
```

### 8.2 Intent Keywords

```python
intent_keywords = {
    'provision': ['provision', 'create', 'deploy', 'setup', 'launch', 'spin up'],
    'analyze':   ['analyze', 'review', 'check', 'examine', 'inspect', 'audit'],
    'optimize':  ['optimize', 'improve', 'reduce', 'minimize', 'enhance'],
    'troubleshoot': ['fix', 'resolve', 'debug', 'troubleshoot', 'error', 'issue'],
    'monitor':   ['monitor', 'status', 'health', 'metrics', 'performance'],
    'cost':      ['cost', 'billing', 'price', 'spend', 'budget', 'expensive']
}
```

### 8.3 Reasoning Response Structure

```json
{
  "query": "Provision a Kubernetes cluster with 3 nodes in us-west-1",
  "intent": "provision",
  "steps": [
    {
      "type": "analyze",
      "content": "Detected intent: provision (Kubernetes cluster)",
      "confidence": 0.95,
      "metadata": {"intent": "provision", "resource": "kubernetes"}
    },
    {
      "type": "context",
      "content": "Found 5 similar deployment configurations...",
      "confidence": 0.85,
      "metadata": {"matches": 5}
    },
    {
      "type": "synthesize",
      "content": "Recommended: EKS cluster, t3.large nodes, us-west-1...",
      "confidence": 0.90
    }
  ],
  "final_answer": "Based on similar deployments, I recommend...",
  "confidence": 0.90,
  "context_used": "5 deployment templates, 2 knowledge base entries"
}
```

---

## 9. API Reference

### 9.1 ML Service Endpoints

#### V1 - General Purpose

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/query` | General query with optional reasoning |
| POST | `/api/v1/developer` | IaC generation (Terraform examples) |
| POST | `/api/v1/terminal` | Terminal commands & incident troubleshooting |

**POST /api/v1/query**
```json
Request:
{
  "query": "Deploy a small EC2 instance with 30GB disk",
  "include_reasoning": true,
  "top_k": 5
}

Response:
{
  "response": "Based on your request, I recommend...",
  "reasoning": {
    "intent": "provision",
    "confidence": 0.92,
    "steps": [...]
  },
  "context": [
    {"text": "...", "score": 0.88, "metadata": {...}}
  ]
}
```

#### V2 - NLP & Document Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v2/query` | Query with entity extraction |
| POST | `/api/v2/extract` | Extract cloud/DevOps entities from text |
| POST | `/api/v2/upload` | Analyze documents (images, PDFs, configs) |
| GET | `/api/v2/status` | NLP system capabilities |

#### V3 - Cloud/DevOps Incident Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v3/query` | Incident pattern analysis with multi-model ML |

**ML Models Used in V3:**
- Sklearn IsolationForest (anomaly detection)
- XGBoost (severity prediction)
- PyTorch embeddings (query similarity)

### 9.2 Cloud Provisioning Intent API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cloud/provision-intent` | Translate query to provisioning payload |

**POST /api/cloud/provision-intent**
```json
Request:
{
  "query": "Provision a Kubernetes cluster with 3 nodes in us-west-1"
}

Response:
{
  "query_type": "provisioning",
  "intent": "provision_kubernetes",
  "confidence": 0.85,
  "payload": {
    "username": "user",
    "workspace": "workspace",
    "cluster_name": "cluster-xyz",
    "node_count": 3,
    "node_type": "t3.large",
    "region": "us-west-1",
    "cloud_provider": "aws",
    "kubernetes_version": "1.29"
  },
  "match_prompt": "Create an EKS cluster, 2 nodes, m5.large"
}
```

**Non-Provisioning Response:**
```json
{
  "query_type": "incident",
  "intent": null,
  "payload": null,
  "confidence": 0.15,
  "match_prompt": ""
}
```

### 9.3 Platform Management API

#### Model Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/platform/models/` | List all models (with state filter) |
| POST | `/platform/models/` | Create new model |
| GET | `/platform/models/{model_id}` | Get model details |
| DELETE | `/platform/models/{model_id}` | Soft delete model |
| POST | `/platform/models/{model_id}/restore` | Restore deleted model |
| PATCH | `/platform/models/{model_id}/alias` | Rename model alias |
| PATCH | `/platform/models/{model_id}/state` | Update state (DRAFT/PRODUCTION/ARCHIVED) |
| GET | `/platform/models/{model_id}/export` | Export training data as JSONL |

**Required Header:** `X-Tenant-ID: <tenant_id>`

**Model States:**
```
DRAFT --> PRODUCTION --> ARCHIVED
  ^                        |
  +--- (restore) ----------+
```

#### Evaluation / Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/platform/evals/feedback` | Submit human feedback |
| GET | `/platform/evals/feedback/{eval_id}` | Get feedback record |
| GET | `/platform/evals/feedback/model/{model_id}` | List feedback by model |
| GET | `/platform/evals/stats` | Get evaluation statistics |

### 9.4 Service Integration Endpoints

#### Redis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/redis/set` | Set key-value pair |
| GET | `/redis/get?key=...` | Get value by key |
| DELETE | `/redis/delete?key=...` | Delete key |
| GET | `/redis/list` | List all keys |

#### RabbitMQ

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rabbitmq/publish` | Publish message to queue |
| POST | `/rabbitmq/queue/declare` | Declare a new queue |
| GET | `/rabbitmq/queue/{name}` | Get queue info |
| GET | `/rabbitmq/health` | Health check |

#### Kafka

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/kafka/tenant/event/publish` | Publish cloud infrastructure event |
| POST | `/kafka/tenant/events/batch` | Batch publish events |
| GET | `/kafka/event/redis` | Get cached event from Redis |
| GET | `/kafka/tenant/events` | Get all tenant events |

#### Celery

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/celery/task/submit` | Submit async task |
| GET | `/celery/task/status?task_id=...` | Get task status |
| GET | `/celery/task/list` | List all tasks |

### 9.5 Monitoring Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/monitoring/metrics` | Prometheus-format metrics |
| GET | `/monitoring/metrics/json` | JSON-format metrics |
| GET | `/monitoring/performance` | Current system performance |
| GET | `/monitoring/performance/response-times` | Response time statistics |
| GET | `/monitoring/performance/errors` | Error statistics |
| GET | `/monitoring/logs` | Query logs with filters |
| GET | `/monitoring/logs/stats` | Log statistics by level/hour |
| GET | `/monitoring/logs/errors` | Recent errors |
| GET | `/monitoring/logs/tail` | Tail last N log lines |
| GET | `/monitoring/logs/file/download` | Download log file |
| GET | `/monitoring/health` | System health check |
| GET | `/monitoring/observability/status` | OpenTelemetry status |

### 9.6 Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |
| GET | `/platform/health/models/{model_id}/status` | Model health |
| GET | `/platform/health/models/status` | All model statuses |
| POST | `/platform/health/models/{model_id}/warm` | Manual model warm-up |

---

## 10. Multi-Provider LLM Support

### 10.1 Supported Providers

| Provider | Models | API Key Env Var |
|----------|--------|----------------|
| **OpenAI** | gpt-5, gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo | `OPENAI_API_KEY` |
| **Anthropic** | claude-4.5, claude-3-5-sonnet, claude-3-opus, claude-3-haiku | `ANTHROPIC_API_KEY` |
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash | `GOOGLE_API_KEY` |
| **Qwen (Alibaba)** | qwen-max, qwen-plus, qwen-turbo, qwen3-omni | `QWEN_API_KEY` |
| **DeepSeek** | deepseek-chat, deepseek-coder | `DEEPSEEK_API_KEY` |
| **Ollama** | llama3.1, mistral, phi-3 (local) | N/A (local) |
| **HuggingFace** | Qwen2.5-3B, Qwen2.5-7B (local) | N/A (local) |

### 10.2 Model Capabilities

| Capability | Description |
|-----------|-------------|
| TEXT_GENERATION | Generate text completions |
| CHAT | Multi-turn conversations |
| FUNCTION_CALLING | Tool/function invocation |
| VISION | Image understanding |
| AUDIO_INPUT | Speech recognition |
| AUDIO_OUTPUT | Speech synthesis |
| SPEECH_TO_SPEECH | Real-time voice conversations |
| STREAMING | Token-by-token streaming |
| EMBEDDINGS | Vector embeddings generation |
| CODE_GENERATION | Code writing and analysis |
| REASONING | Chain-of-thought reasoning |
| MULTIMODAL | Combined text + image + audio |

### 10.3 Voice Agent Support

| Model | Type | Use Case |
|-------|------|----------|
| Qwen3-Omni | Speech-to-speech | Real-time voice conversations with barge-in |
| Qwen3-ASR | Speech recognition | Transcription |
| Qwen3-TTS | Text-to-speech | Voice output |
| Faster Whisper | Local ASR | Offline speech recognition |
| Kokoro | Local TTS | Offline text-to-speech |

### 10.4 Cost Estimation

```python
# Estimate cost for a model call
cost = estimate_cost(
    model_id="gpt-4o",
    input_tokens=1000,
    output_tokens=500
)
# Returns cost in USD based on per-1K-token pricing
```

---

## 11. Reinforcement Learning with Human Feedback (RLHF)

### 11.1 RLHF Pipeline Overview

```
+------------------+     +------------------+     +------------------+
| User Query       | --> | Model Inference  | --> | User Response    |
+------------------+     +------------------+     +------------------+
                                                         |
                                                         v
+------------------+     +------------------+     +------------------+
| Fine-Tune Model  | <-- | Export JSONL     | <-- | Human Feedback   |
| (train.py)       |     | Training Data    |     | (Thumbs Up/Down) |
+------------------+     +------------------+     +------------------+
```

### 11.2 Feedback Collection

**Submit Feedback:**
```json
POST /platform/evals/feedback
Headers: X-Tenant-ID: tenant-123

{
  "request_id": "req-abc123",
  "model_id": "model-456",
  "feedback_type": "THUMBS_UP",
  "feedback_value": 1,
  "feedback_text": "Accurate provisioning recommendation",
  "response_time_ms": 150.5,
  "token_count": 42,
  "reasoning_steps": 5,
  "query": "Deploy a t3.medium in us-west-2",
  "response": "Provisioning initiated with EKS cluster...",
  "prompt": "System prompt used..."
}
```

**Feedback Types:**
| Type | Value | Meaning |
|------|-------|---------|
| THUMBS_UP | 1 | Positive signal - correct response |
| THUMBS_DOWN | -1 | Negative signal - incorrect response |
| CUSTOM | 0 | Neutral with text explanation |

### 11.3 Evaluation Statistics

```json
GET /platform/evals/stats?model_id=model-456

Response:
{
  "total_feedback": 100,
  "thumbs_up": 85,
  "thumbs_down": 15,
  "custom": 0,
  "satisfaction_rate": 85.0,
  "avg_response_time_ms": 125.3,
  "avg_tokens": 38.5
}
```

### 11.4 Training Data Export (JSONL)

```json
GET /platform/models/{model_id}/export?include_feedback_only=true

Output (one JSON per line):
{
  "request_id": "req-abc123",
  "timestamp": "2026-02-07T10:15:00Z",
  "query": "Deploy a t3.medium in us-west-2",
  "prompt": "You are an AI assistant for cloud provisioning...",
  "response": "I recommend deploying a t3.medium EC2 instance...",
  "tokens": {"input": 150, "output": 200, "total": 350},
  "performance": {"latency_ms": 150.5},
  "feedback": {
    "type": "THUMBS_UP",
    "value": 1,
    "text": "Accurate recommendation",
    "reasoning_steps": 5
  }
}
```

### 11.5 RLHF Retraining Workflow

1. **Collect Feedback** - Users rate responses via thumbs up/down
2. **Export Training Data** - `GET /platform/models/{model_id}/export?include_feedback_only=true`
3. **Filter by Quality** - Keep THUMBS_UP responses as positive examples
4. **Augment Datasets** - Add exported JSONL to `app/data/datasets/`
5. **Retrain Model** - Run `python -m app.services.ai.ml.train`
6. **Rebuild Index** - Run `python -m app.services.ai.ml.precompute`
7. **Deploy New Model** - Update model state to PRODUCTION
8. **Monitor Performance** - Track satisfaction_rate over time

### 11.6 Request Logging for RLHF

Every API request is automatically logged with:

| Field | Description |
|-------|-------------|
| request_id | Unique request identifier |
| tenant_id | Tenant making the request |
| model_id | Model used for inference |
| query | User's original query |
| prompt | Full prompt sent to model |
| response | Model's response |
| tokens_input | Input token count |
| tokens_output | Output token count |
| latency_ms | Response latency |
| log_metadata | Additional context (JSON) |

This data enables:
- **Performance tracking** per model and tenant
- **Quality analysis** when combined with feedback
- **Training data generation** for fine-tuning
- **A/B testing** across model versions

---

## 12. Service Integrations

### 12.1 Redis

**Purpose:** Caching, rate limiting, Celery broker

**Configuration:**
```
REDIS_HOST: localhost (default)
REDIS_PORT: 6379
REDIS_PASSWORD: (from env)
```

**Usage in VaLLM:**
- Embedding cache (avoid re-encoding)
- Search result cache
- Tenant rate limit tracking (TPM/RPM)
- Celery task broker and result backend
- Kafka event caching

### 12.2 RabbitMQ

**Purpose:** AMQP messaging for task distribution

**Configuration:**
```
RABBITMQ_HOST: localhost (default)
RABBITMQ_PORT: 5672
RABBITMQ_USER: guest
RABBITMQ_PASSWORD: guest
```

**Features:**
- Persistent message delivery (delivery_mode=2)
- Auto-reconnection
- Durable queues

### 12.3 Kafka

**Purpose:** High-throughput cloud infrastructure event streaming

**Topics:**
| Topic | Events |
|-------|--------|
| infrastructure-events | REQUESTED, PROVISIONING, READY, FAILED |
| scaling-events | REQUESTED, IN_PROGRESS, COMPLETED |
| monitoring-events | ALERT |
| backup-events | STARTED, COMPLETED |
| cost-analytics | Cost tracking events |
| security-events | Security alerts |
| compliance-events | Compliance logging |

**Features:**
- Idempotent producer writes
- GZIP compression
- Redis caching of recent events
- PostgreSQL audit logging
- Tenant-aware event partitioning

### 12.4 Celery

**Purpose:** Distributed async task execution

**Configuration:**
```
Broker: Redis
Result Backend: Redis
Serializer: JSON
Concurrency: Configurable
```

**Features:**
- Tenant-aware task submission with priority
- Batch task submission
- Task throttling per tenant (max_concurrent=3)
- Task status tracking and cancellation

### 12.5 PostgreSQL

**Purpose:** Primary persistent storage

**Connection Pooling:**
```
Pool Size: 10 (default) / 20 (platform)
Max Overflow: 20 (default) / 30 (platform)
Pool Pre-Ping: true
Driver: asyncpg (async) / psycopg2 (sync)
```

**Database Tables:**
| Table | Purpose |
|-------|---------|
| tenants | Multi-tenant isolation |
| models | LLM model registry |
| model_metadata | Model UI and performance config |
| evals | Human feedback records |
| request_logs | API request logging for RLHF |

---

## 13. Monitoring & Observability

### 13.1 Prometheus Metrics

**HTTP Metrics:**
- `http_requests_total{method, endpoint, status}` - Request counter
- `http_request_duration_seconds{method, endpoint}` - Latency histogram

**ML Metrics:**
- `vector_search_requests_total` - Search counter
- `vector_search_duration_seconds` - Search latency
- `llm_generation_requests_total` - LLM call counter

**Cache Metrics:**
- `cache_hits_total{cache_type}` - Cache hit counter
- `cache_misses_total{cache_type}` - Cache miss counter

**System Metrics:**
- `active_connections{connection_type}` - Active connection gauge
- `memory_usage_bytes{component}` - Memory usage gauge
- `cpu_usage_percent{component}` - CPU usage gauge

### 13.2 Performance Monitoring

**Real-time metrics collected every 5 seconds:**
- CPU utilization (%)
- Memory usage (bytes and %)
- Disk I/O (read/write bytes)
- Network I/O (sent/received bytes)
- Response time percentiles (p50, p95, p99)
- Error rates by endpoint

**Alert Thresholds:**
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU | > 80% | Alert |
| Memory | > 80% | Alert |
| Response Time | > 1.0s | Alert |

### 13.3 Structured Logging

**JSON logging** enabled via `VALLM_JSON_LOGGING=true`:
```json
{
  "timestamp": "2026-02-07T12:00:00Z",
  "level": "INFO",
  "message": "Query processed",
  "request_id": "req-abc123",
  "trace_id": "trace-xyz",
  "service": "vallm",
  "duration_ms": 150
}
```

**Log Rotation:** Midnight rotation, 30-day retention

### 13.4 OpenTelemetry

**Configuration:**
```
OTEL_ENABLED: true/false
OTEL_SERVICE_NAME: vallm (default)
OTEL_EXPORTER_OTLP_ENDPOINT: http://localhost:4318
```

Exports traces and metrics via OTLP HTTP protocol.

---

## 14. Deployment Guide

### 14.1 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Run with Docker Compose
docker-compose up -d
```

### 14.2 Docker Deployment

```bash
# Build image
docker build -t vallm:latest .

# Run container
docker run -d \
  --name vallm \
  -p 8000:8000 \
  -v $(pwd)/app/data:/app/data \
  -e ENVIRONMENT=production \
  -e OPENAI_API_KEY=sk-... \
  vallm:latest

# Health check
curl http://localhost:8000/health
```

### 14.3 Kubernetes (AWS EKS)

**Prerequisites:**
- AWS CLI configured
- kubectl configured for EKS
- ECR repository created

```bash
# Apply manifests
kubectl apply -f deployment/kubernetes/eks/deploy_kubernetes_eks.yml

# Verify deployment
kubectl get pods -n vallm-production
kubectl rollout status deployment/vallm-api -n vallm-production
```

**Key Features:**
- 3 replicas (auto-scales to 50 via HPA)
- 100Gi EFS persistent storage
- NLB with SSL termination
- CronJobs for data pipeline (S3 fetcher, URL fetcher, processor)
- Pod Disruption Budget (minAvailable: 2)
- Network policies for security

### 14.4 Kubernetes (Azure AKS)

**Prerequisites:**
- Azure CLI configured
- kubectl configured for AKS
- ACR repository created

```bash
# Apply manifests
kubectl apply -f deployment/kubernetes/aks/deploy_kubernetes_aks.yml

# Verify deployment
kubectl get pods -n vallm-production
```

**Key Differences from EKS:**
- Azure Managed Identity (instead of IRSA)
- Azure Files CSI storage (instead of EFS)
- Application Gateway ingress (instead of ALB)
- Blob Storage fetcher CronJob (instead of S3)

### 14.5 CI/CD Pipelines

| Pipeline | Trigger | Target |
|----------|---------|--------|
| GitHub Actions | Push to main/production | VM or AKS |
| Azure Pipelines | Push to main | VM or AKS (configurable) |
| GitLab CI | Push to any branch | Docker Hub/Registry |

### 14.6 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | Yes | development/staging/production |
| `DATABASE_HOST` | Yes | PostgreSQL host |
| `DATABASE_PORT` | No | PostgreSQL port (default: 5432) |
| `DATABASE_NAME` | Yes | Database name |
| `DATABASE_USER` | Yes | Database user |
| `DATABASE_PASSWORD` | Yes | Database password |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `GOOGLE_API_KEY` | No | Google Gemini API key |
| `QWEN_API_KEY` | No | Qwen/Alibaba API key |
| `DEEPSEEK_API_KEY` | No | DeepSeek API key |
| `REDIS_HOST` | No | Redis host (default: localhost) |
| `REDIS_PORT` | No | Redis port (default: 6379) |
| `REDIS_PASSWORD` | No | Redis password |
| `AWS_ACCESS_KEY_ID` | No | AWS access key (for S3) |
| `AWS_SECRET_ACCESS_KEY` | No | AWS secret key |
| `AWS_REGION` | No | AWS region (default: us-east-1) |
| `S3_BUCKET` | No | S3 bucket for datasets |
| `VALLM_RATE_LIMIT_ENABLED` | No | Enable rate limiting (default: false) |
| `VALLM_RATE_LIMIT_PER_MINUTE` | No | Requests per minute (default: 60) |
| `VALLM_JSON_LOGGING` | No | Enable JSON structured logging |
| `OTEL_ENABLED` | No | Enable OpenTelemetry |

---

## 15. Dataset Schema Reference

### 15.1 Training Data Format for RLHF

**JSONL Export Format (one JSON object per line):**

```json
{
  "request_id": "string",
  "timestamp": "ISO 8601 datetime",
  "query": "User's natural language query",
  "prompt": "Full system prompt + user query",
  "response": "Model's generated response",
  "tokens": {
    "input": 150,
    "output": 200,
    "total": 350
  },
  "performance": {
    "latency_ms": 150.5
  },
  "feedback": {
    "type": "THUMBS_UP | THUMBS_DOWN | CUSTOM",
    "value": 1,
    "text": "Optional feedback text",
    "reasoning_steps": 5
  }
}
```

### 15.2 Database Schema (SQLAlchemy Models)

**Tenant:**
```
id: String (PK)
name: String
is_active: Boolean (default: true)
tpm_limit: Integer (tokens/minute limit)
rpm_limit: Integer (requests/minute limit)
created_at: DateTime
updated_at: DateTime
```

**Model:**
```
id: UUID (PK)
tenant_id: String (FK -> Tenant)
alias: String (unique per tenant)
model_path: String
state: Enum (DRAFT, PRODUCTION, ARCHIVED)
version: String (semantic version)
description: Text
created_by: String
is_deleted: Boolean (soft delete)
deleted_at: DateTime
created_at: DateTime
updated_at: DateTime
```

**ModelMetadata:**
```
id: UUID (PK)
model_id: UUID (FK -> Model)
ui_config_version: String
ui_config: JSON
supports_streaming: Boolean
supports_function_calling: Boolean
max_tokens: Integer (default: 2048)
temperature_range: JSON {"min": 0.0, "max": 2.0}
prompt_fields: JSON
avg_latency_ms: Float
avg_tokens_per_second: Float
accuracy_score: Float
```

**Eval (Feedback):**
```
id: UUID (PK)
request_id: String (FK -> RequestLog)
model_id: UUID (FK -> Model)
tenant_id: String (FK -> Tenant)
feedback_type: Enum (THUMBS_UP, THUMBS_DOWN, CUSTOM)
feedback_value: Integer (-1 to 1)
feedback_text: Text
query: Text
response: Text
prompt: Text
eval_metadata: JSON
response_time_ms: Float
token_count: Integer
reasoning_steps: Integer
created_at: DateTime
```

**RequestLog:**
```
id: UUID (PK)
request_id: String
tenant_id: String (FK -> Tenant)
model_id: UUID
endpoint: String
method: String
query: Text
prompt: Text
response: Text
tokens_used: Integer
tokens_input: Integer
tokens_output: Integer
latency_ms: Float
status_code: Integer
log_metadata: JSON
created_at: DateTime
```

---

## 16. Appendix: Intent-to-Response Mapping Table

This table serves as the primary reference for reinforcement learning. Each row maps a user intent pattern to the expected system behavior.

### 16.1 Provisioning Intents

| # | User Query Pattern | Expected Intent | Expected Payload Keys | Expected Response Pattern |
|---|-------------------|----------------|----------------------|--------------------------|
| 1 | "Deploy/Create/Provision a [size] EC2/VM instance in [region]" | provision_vm | instance_type, region, cloud_provider, os, volume_size | "Provisioning VM: {instance_type} in {region} on {cloud_provider}" |
| 2 | "Spin up a [size] instance with [os] and [volume]GB disk" | provision_vm | instance_type, os, volume_size, volume_type | "Creating {os} instance ({instance_type}) with {volume_size}GB {volume_type}" |
| 3 | "Create a Kubernetes/K8s/EKS/AKS cluster with [N] nodes" | provision_kubernetes | cluster_name, node_count, node_type, kubernetes_version | "Provisioning K8s cluster: {node_count} x {node_type} nodes" |
| 4 | "Deploy [image] Docker container on [host]" | provision_docker | docker_image, container_name, ports | "Deploying container {container_name} from {docker_image}" |
| 5 | "Set up PostgreSQL/MySQL/MongoDB database on [host]" | provision_database | database_engine, database_name, database_user, port | "Creating {database_engine} database: {database_name}" |
| 6 | "Deploy a FastAPI/API application on [host]" | provision_fastapi | app_name, app_port, http_port, hostname | "Deploying API {app_name} on port {app_port}" |
| 7 | "Host a static website on [host]" | provision_static_website | server_name, http_port, hostname | "Setting up static site: {server_name}" |

### 16.2 Non-Provisioning Intents

| # | User Query Pattern | Expected Query Type | Expected Response Pattern |
|---|-------------------|--------------------|--------------------------|
| 8 | "What caused the [service] error/outage?" | incident | "Root cause: {root_cause}. Resolution: {resolution}" |
| 9 | "Show me cost/spend for [service/account]" | cost | "Cost analysis: {breakdown}. Optimization: {recommendations}" |
| 10 | "What are my billing/charges for [period]?" | billing | "Billing summary: {charges}. Details: {breakdown}" |
| 11 | "Is [service] secure? Any vulnerabilities?" | security | "Security assessment: {findings}. Recommendations: {actions}" |
| 12 | "What do you recommend for [use case]?" | recommendation | "Based on best practices: {recommendations}" |
| 13 | "Monitor/status/health of [service]" | other (monitor) | "Current status: {metrics}. Health: {status}" |

### 16.3 Complex Multi-Step Intents

| # | User Query Pattern | Classification | System Behavior |
|---|-------------------|---------------|-----------------|
| 14 | "Set up a production-ready environment with HA" | provision_vm + provision_kubernetes | Multi-step: identify all resources, generate payloads for each |
| 15 | "Our API is down, fix it" | incident (troubleshoot) | Search incident KB, find similar outages, provide resolution steps |
| 16 | "Optimize our AWS costs" | cost (optimize) | Analyze resource usage, identify waste, recommend rightsizing |
| 17 | "We need HIPAA compliance for our database" | security (compliance) | Recommend encryption, audit logging, VPC isolation, PrivateLink |

### 16.4 Reward Signals for RLHF

| Signal | Source | Weight | Description |
|--------|--------|--------|-------------|
| **Thumbs Up** | User feedback | +1.0 | User confirms response was helpful/accurate |
| **Thumbs Down** | User feedback | -1.0 | User indicates response was wrong/unhelpful |
| **Response Time** | System metric | 0.1-0.5 | Faster responses get higher reward |
| **Confidence Score** | Model output | 0.0-1.0 | Higher confidence on correct answers = bonus |
| **Token Efficiency** | System metric | 0.1-0.3 | Concise, accurate responses preferred |
| **Reasoning Steps** | Model output | 0.0-0.5 | Appropriate depth of reasoning |
| **Intent Accuracy** | Post-hoc eval | +1.0/-1.0 | Did the detected intent match the actual need? |
| **Payload Validity** | Agent validation | +1.0/-1.0 | Was the generated payload valid for Golang API? |

### 16.5 Training Dataset Statistics

| Metric | Value |
|--------|-------|
| Total training samples | ~2,500+ (cloud_deployments.csv) |
| Incident records | ~50 (cloud_observability.csv) |
| Deployment use cases | ~100+ (deployments.json) |
| Knowledge base entries | 2 files (provisioning knowledge) |
| Embedding dimensions | 384 |
| FAISS index type | IndexFlatIP (cosine similarity) |
| Confidence threshold | 0.2 |
| Intent categories | 6 provisioning + 5 non-provisioning |

---

## Quick Reference Card

### Most Common Operations

```bash
# Health check
curl http://localhost:8000/health

# Query with reasoning
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Deploy a t3.medium EC2 in us-east-1", "include_reasoning": true}'

# Get provisioning intent
curl -X POST http://localhost:8000/api/cloud/provision-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a Kubernetes cluster with 3 nodes"}'

# Submit feedback
curl -X POST http://localhost:8000/platform/evals/feedback \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: my-tenant" \
  -d '{"request_id": "req-123", "model_id": "model-456", "feedback_type": "THUMBS_UP", "feedback_value": 1}'

# Export training data
curl http://localhost:8000/platform/models/model-456/export?include_feedback_only=true \
  -H "X-Tenant-ID: my-tenant"

# Prometheus metrics
curl http://localhost:8000/monitoring/metrics

# Rebuild FAISS index
python -m app.services.ai.ml.precompute

# Retrain model
python -m app.services.ai.ml.train

# Generate synthetic training data
python scripts/generate_cloud_deployments.py --rows 5000
```

---

*Document generated: 2026-02-07*
*VaLLM Version: 1.0.0*
*For questions, submit feedback via the evaluation API or contact the platform team.*
