# VxThinkingLLM — ProdxCloud Multi-Model Platform (3 + 1)

> **Mission**: A sovereign, production-grade AI platform that ships **three fine-tuned specialist LLMs** (cloud, code, support) coordinated by **one reasoning core** (VxThinking). Grounded in *your* private data via FAISS vector search and chain-of-thoughts reasoning — no external API calls, no data leaving your network.

---

## Table of Contents

- [The 3 + 1 Models](#the-3--1-models)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Training the Models](#training-the-models)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Docs-grounded Q&A](#docs-grounded-qa-vxcloudio)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## The 3 + 1 Models

VxThinkingLLM bundles four cooperating models. The **+1 core** does retrieval, planning, and reasoning; the **3 specialists** are fine-tuned causal LMs each focused on one job. A universal `/v1/ask` dispatcher classifies prompts and forwards them to the right backend.

| Model | Role | Base / Arch | Fine-tuned on | Routes |
|-------|------|-------------|---------------|--------|
| **VxThinking v1.2** *(core)* | RAG + planning + chain-of-thought reasoning, ticket/sprint/forecast intelligence. Powers the FAISS-backed RAG endpoints. | GPT-2 (6 layers, 768 hidden, 50 257 vocab) — `app/data/models/thinkingllm/` | Your CSVs/text under `app/data/datasets/thinkingllm/` | `/generate`, `/api/models/v1/*`, `/api/models/v2/*`, `/api/models/v3/*`, `/api/cloud/provision-intent` |
| **VxCloud v1.0** | DevOps / IaC / SRE specialist — Terraform, Kubernetes, Helm, Ansible, runbooks, cost optimization. Hard rule: every security-relevant line is annotated, K8s manifests always include `resources.limits`, IAM is least-privilege. | Qwen2 0.5B (24 layers, 896 hidden, 151 936 vocab) — `app/data/models/cloudllm/` | `app/data/datasets/cloudllm/` | `/v1/cloud/*` |
| **VxCoder v1.0** | Code generation, multi-file edits via XML SEARCH/REPLACE diffs, PR review, test writing (pytest / vitest). | Qwen2 0.5B — `app/data/models/codingllm/` (fallback `Qwen/Qwen2.5-0.5B-Instruct`) | `app/data/datasets/codingllm/` (generator: `scripts/gen_codingllm_dataset.py`) | `/v1/coding/*` |
| **VxSupport v1.0** | IT support / docs Q&A / runbook lookup / Jira-style ticket auto-answer. Always answers in **Diagnosis → Steps → Verify → Escalate** format with cited sources. | Qwen2 0.5B — `app/data/models/supportllm/` (fallback `Qwen/Qwen2.5-0.5B-Instruct`) | `app/data/datasets/supportllm/` (generator: `scripts/gen_supportllm_dataset.py`) | `/v1/support/*` |

Each specialist gracefully **falls back** to its base HF model if no fine-tuned weights are present, so every route is reachable from a clean checkout.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client / Agent                             │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTP
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI gateway  (app/app.py)                                   │
│  ─ logging, request-id, CORS, rate-limit, metrics ─              │
└─┬──────────────┬─────────────┬─────────────┬─────────────┬───────┘
  │              │             │             │             │
  ▼              ▼             ▼             ▼             ▼
/v1/ask     /generate     /v1/cloud     /v1/coding    /v1/support
universal   VxThinking    VxCloud       VxCoder       VxSupport
dispatcher    + RAG       (Qwen2)       (Qwen2)       (Qwen2)
                  │
                  ▼
        FAISS index (all-MiniLM-L6-v2)
        L1 embeddings cache · L2 search cache
                  │
                  ▼
        ReasoningEngine (search → analyze → synthesize → decide)
```

The 3 specialists share `SpecialistBackend` (`app/services/ai/ml/specialist_base.py`) so load + generate behavior is identical line-for-line; the only per-model differences are **path**, **fallback base model**, and **system prompt**.

---

## Quick Start

```bash
# 1. Install
python -m venv venv
source venv/bin/activate            # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Run (auto-precompute + auto-train kick in if data is present)
python -m app.app
# → http://localhost:8745
```

Welcome page: <http://localhost:8745/> · OpenAPI: <http://localhost:8745/docs> · ReDoc: <http://localhost:8745/redoc>

```bash
# 3. Smoke-test all four models
python scripts/smoke_test_specialists.py
python scripts/smoke_test_two.py

# 4. Try the universal dispatcher
curl -s http://localhost:8745/v1/ask \
  -H 'content-type: application/json' \
  -d '{"prompt":"Write a Terraform module for an S3 bucket with KMS"}' | jq .
```

---

## Training the Models

Each model has its own `train.py` and dataset directory.

```bash
# Generate synthetic specialist datasets (run once)
python scripts/gen_codingllm_dataset.py
python scripts/gen_supportllm_dataset.py

# Train each model
python -m app.services.ai.ml.train                    # VxThinking core
python -m app.services.ai.ml.cloudllm.train           # VxCloud
python -m app.services.ai.ml.codingllm.train          # VxCoder
python -m app.services.ai.ml.supportllm.train         # VxSupport

# Build the FAISS index for VxThinking RAG
python -m app.services.ai.ml.precompute
```

**Auto-train** is on by default — if `app/data/models/thinkingllm/config.json` is missing on startup and a dataset is present, training launches automatically (set `VxThinkingLLM_AUTO_TRAIN=false` to disable).

### Train on real VxCloud + SalesShift knowledge

`app.services.ai.ml.train` reads **every** `.csv/.json/.txt/.md` under `app/data/datasets/` (recursively, so each specialist subfolder is included) and fine-tunes a causal LM on it. To (re)train on the live product docs — DevOps **and** customer-service — regenerate the corpus from the retrieval index, then train:

```bash
python -m app.services.docs.build                     # 1. refresh the combined index (both sites)
python scripts/ml/build_knowledge_dataset.py          # 2. index + llms.txt + vxnode runbook → app/data/datasets/supportllm/ (~15k examples)
python -m app.services.ai.ml.train \                  # 3. fine-tune (continue from the current weights)
  --model-name-or-path app/data/models/cloudllm \
  --output-dir app/data/models/cloudllm_support \
  --max-steps 250                                     #    --max-steps caps CPU runs; drop it for a full epoch
```

Point `CLOUDLLM_MODEL_PATH` at the new dir to serve it. The 6-layer GPT-2 fallback is tiny — it adapts to the domain's vocabulary but is **not** a reliable answerer; grounded answers come from the retrieval index (extractive mode), and real generative answers need a chat model (e.g. `Qwen2.5-Instruct`) via `CLOUDLLM_MODEL_PATH` + `mode: "llm"`.

---

## Deployment

```bash
# Single node (dev)
python -m app.app

# Production (uvicorn)
uvicorn app.app:app --host 0.0.0.0 --port 8745 --workers 4

# Docker
docker compose up -d
# or
docker build -t vxthinkingllm:latest . && docker run -p 8745:8745 vxthinkingllm:latest
```

GPU is auto-detected (`USE_CUDA=true` to force). All four models share the device chosen at startup.

---

## API Reference

> **Tip:** the universal `POST /v1/ask` endpoint will pick the right model for you. Use the per-model endpoints below when you need fine control over parameters or specialist-specific request shapes.

### Platform — system

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | HTML welcome page (model overview + quick links) |
| `GET` | `/health` | Liveness probe |
| `GET` | `/stats` | Vector store + cache statistics |
| `GET` | `/logs` | Recent log lines (`?lines=50`) |
| `GET` | `/logs/stats` | Log counts (requests, responses, errors) |
| `DELETE` | `/logs/clear` | Truncate the log file |
| `GET` | `/docs` · `/redoc` | OpenAPI / ReDoc UIs |

### Platform — direct generation & search (VxThinking)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/generate` | Direct text generation on the VxThinking core (LangChain-compatible response with `text` alias) |
| `POST` | `/search` | FAISS vector similarity search (`{query, top_k}`) |

### VxThinking — V1 (RAG + reasoning)

Mounted at `/api/models/v1`.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/models/v1/query` | RAG query with chain-of-thought reasoning |
| `POST` | `/api/models/v1/developer` | Developer assistance (RAG + code-oriented prompt) |
| `POST` | `/api/models/v1/terminal` | Terminal / CLI assistance |

### VxThinking — V2 (NLP + document analysis)

Mounted at `/api/models/v2`.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/models/v2/query` | NLP-enhanced query (entity-aware) |
| `POST` | `/api/models/v2/extract` | Entity extraction (spaCy, optional) |
| `POST` | `/api/models/v2/upload` | Document / image upload (added to vector store) |
| `GET` | `/api/models/v2/status` | NLP capability status |

### VxThinking — V3 (incident patterns)

Mounted at `/api/models/v3`.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/models/v3/query` | Unusual cloud / DevOps incident-pattern detection with metrics |

### Cloud provisioning bridge

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/cloud/provision-intent` | Returns intent classification + Golang payload for the provisioning agent. `query_type` ∈ `incidents \| cost \| billing \| security \| recommendations` |

### VxCloud — `/v1/cloud`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/cloud/health` | Backend status, loaded model, device, paths |
| `POST` | `/v1/cloud/generate` | Direct cloud-specialist generation |
| `POST` | `/v1/cloud/query` | Generation + richer payload (`raw`, `loaded_from`, `duration_ms`) |

### VxCoder — `/v1/coding`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/coding/health` | Backend status |
| `POST` | `/v1/coding/generate` | Code generation (accepts `language`, `framework`) |
| `POST` | `/v1/coding/edit` | Multi-file edit; returns XML SEARCH/REPLACE diffs |
| `POST` | `/v1/coding/review` | Diff review (correctness · security · readability) |

### VxSupport — `/v1/support`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/support/health` | Backend status |
| `POST` | `/v1/support/generate` | Free-form support question |
| `POST` | `/v1/support/ticket` | Answer a Jira-style ticket (`title`, `body`, `reporter`, `labels`) |
| `POST` | `/v1/support/runbook` | Runbook lookup (Diagnosis → Steps → Verify → Escalate) |

### Universal dispatcher — `/v1`

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/ask` | Classifies the prompt and forwards to the right model. Use `force_model` to override (`thinkingllm \| cloudllm \| codingllm \| supportllm`) |
| `GET` | `/v1/ask/routes` | Inspect the keyword routing table |

### Monitoring — `/monitoring`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/monitoring/` · `/monitoring/health` · `/monitoring/status` | Service health and observability summary |
| `GET` | `/monitoring/metrics` · `/monitoring/metrics/prometheus` · `/monitoring/metrics/json` | Prometheus / JSON metrics |
| `POST` | `/monitoring/metrics/test` | Emit synthetic metrics |
| `GET` | `/monitoring/performance` · `/current` · `/response-times` · `/errors` · `/history` | Performance counters |
| `POST` | `/monitoring/performance/test` | Synthetic perf event |
| `GET` | `/monitoring/logs` · `/stats` · `/errors` · `/warnings` · `/search` · `/tail` · `/info` · `/file` · `/file/download` | Log inspection |
| `GET` | `/monitoring/observability/status` | Tracing / metrics backend status |

---

## Docs-grounded Q&A (vxcloud.io + SalesShift)

Questions about the products — DevOps ("How do I install vxcli?", "which header authenticates the API?") **and** customer-service ("How much does SalesShift cost?", "How do I send a tracked email?") — are answered from the live docs, not from model weights. One combined index covers **both** sites, so a single `/v1/docs/ask` (and the `/v1/ask` dispatcher) answers either. The pipeline is retrieve → ground → answer:

```
vxcloud.io/docs + salesshift.vxcloud.io/docs   (llms.txt + product/guide pages)
   └─ crawler.py   crawl_sites() merges both sites; HTML → heading-level chunks, code verbatim;
                   CLI/SDK reference read from the Next.js payload (per-command flags/usage/examples)
   └─ index.py     BM25 (title + URL slug + heading + body), stemming, heading-precision boost,
                   product affinity (a query naming vxcli/SalesShift prefers that site's pages)
   └─ answer.py    refuse if weak/uncovered → else LLM answer from excerpts or extractive answer
```

```bash
python -m app.services.docs.build              # crawl BOTH sites + index → data/docs_index/index.json (~40 s, ~1700 chunks)
python -m app.services.docs.build --base-url https://vxcloud.io   # one site only
python -m scripts.eval_docs --min-pass 0.9     # gold-set check (VxCloud + SalesShift); add a case for every bad answer
curl -s localhost:8745/v1/docs/ask -H 'content-type: application/json' \
  -d '{"question":"How much does SalesShift cost?"}' | jq -r .answer
```

> The same corpus feeds training: `python scripts/ml/build_knowledge_dataset.py` serialises the index (plus both `llms.txt` and the vxnode runbook) into `app/data/datasets/supportllm/`, so the specialist can be retrained on real VxCloud + SalesShift knowledge. See [Training the Models](#training-the-models).

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/docs/ask` | `{question, k, mode: auto\|llm\|extractive}` → `answer`, `sources[]`, `mode`, `grounded` |
| `POST /v1/docs/search` | ranked sections, no generation |
| `GET /v1/docs/health` | index status (chunks, pages, built_at) |
| `POST /v1/docs/reindex` | re-crawl; requires `X-Admin-Token` = `$VXDOCS_ADMIN_TOKEN` (disabled when unset) |
| `POST /v1/ask` | prompts mentioning vxcli / vxcloud / prodxcloud / **salesshift** / SDK / etc. are routed to the docs |

**Answer modes.** `extractive` returns the best section verbatim, so commands can't be hallucinated. `llm` puts the top excerpts in the prompt (chat template, greedy) and is accepted only if every command in the output also appears in the excerpts; otherwise it falls back to extractive. `auto` uses `llm` when the loaded model has a chat template (the `distilgpt2` fallback has none, so it serves extractive answers).

| Variable | Default | Effect |
|----------|---------|--------|
| `VXDOCS_INDEX_PATH` | `data/docs_index/index.json` | Index location |
| `VXDOCS_AUTO_INDEX` | `true` | Build the index in the background at startup if missing |
| `VXDOCS_ADMIN_TOKEN` | *(unset)* | Enables `POST /v1/docs/reindex` |
| `DOCS_ANSWER_MODE` | `auto` | Default answer mode |
| `DOCS_MIN_SCORE` / `DOCS_MIN_COVERAGE` | `4.0` / `0.5` | Refusal gate (BM25 floor / share of query terms found) |

Re-index after each docs deploy (CI step: `python -m app.services.docs.build`), not per request.

---

## Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `VxThinkingLLM_AUTO_PRECOMPUTE` | `true` | Build FAISS index on startup if missing |
| `VxThinkingLLM_AUTO_TRAIN` | `true` | Train VxThinking on startup if model is missing |
| `USE_CUDA` | `false` | Use GPU for inference (auto-detected if available) |
| `VxThinkingLLM_CACHE_EMBEDDINGS` | `true` | L1 embedding cache (TTL 1h) |
| `VxThinkingLLM_CACHE_SEARCH` | `true` | L2 search cache (TTL 30m) |
| `VxThinkingLLM_CACHE_EMBEDDINGS_MAXSIZE` | `2000` | L1 max entries |
| `VxThinkingLLM_CACHE_SEARCH_MAXSIZE` | `1000` | L2 max entries |
| `CLOUDLLM_MODEL_PATH` / `_DATASET_DIR` | `app/data/{models,datasets}/cloudllm` | Override VxCloud paths |
| `CODINGLLM_MODEL_PATH` / `_DATASET_DIR` / `_PRECOMPUTE_DIR` | `app/data/{...}/codingllm` | Override VxCoder paths |
| `SUPPORTLLM_MODEL_PATH` / `_DATASET_DIR` / `_PRECOMPUTE_DIR` | `app/data/{...}/supportllm` | Override VxSupport paths |

---

## Project Structure

```
VxThinkingLLM/
├── app/
│   ├── app.py                             # FastAPI gateway (lifespan, routers, welcome page)
│   ├── core/                              # settings, logging
│   ├── data/
│   │   ├── datasets/{thinkingllm,cloudllm,codingllm,supportllm}/
│   │   ├── models/{thinkingllm,cloudllm,codingllm,supportllm}/
│   │   └── precompute/{thinkingllm,codingllm,supportllm}/
│   └── services/
│       ├── ai/ml/
│       │   ├── embeddings.py              # FAISS + sentence-transformers
│       │   ├── reasoning.py               # ReasoningEngine
│       │   ├── routes.py                  # /api/models/v1, v2, v3 routers
│       │   ├── cloud_routes.py            # /api/cloud/provision-intent
│       │   ├── universal.py               # /v1/ask universal dispatcher
│       │   ├── specialist_base.py         # shared HF load/generate base class
│       │   ├── train.py / precompute.py   # VxThinking training / FAISS build
│       │   ├── cloudllm/                  # backend + routes + train (VxCloud)
│       │   ├── codingllm/                 # backend + routes + train (VxCoder)
│       │   └── supportllm/                # backend + routes + train (VxSupport)
│       └── monitoring/                    # Prometheus, perf, logs (/monitoring/*)
├── scripts/
│   ├── gen_codingllm_dataset.py
│   ├── gen_supportllm_dataset.py
│   ├── smoke_test_specialists.py
│   └── smoke_test_two.py
├── nginx/                                 # reverse proxy config
├── Dockerfile · docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Troubleshooting

- **`{"status":"degraded"}` on `/v1/{cloud,coding,support}/health`** — fine-tuned weights are missing; the backend fell back to the HF base model. Run the matching `train.py`.
- **`Vector store not initialized`** on `/search` — set `VxThinkingLLM_AUTO_PRECOMPUTE=true` (default) and add CSV/text to `app/data/datasets/thinkingllm/`, or run `python -m app.services.ai.ml.precompute`.
- **CUDA OOM with all 4 models loaded** — drop one specialist by unsetting its model path so it falls back to CPU, or run on a larger GPU. All four backends share the device chosen at startup.
- **Routing went to the wrong specialist** — call `GET /v1/ask/routes` to inspect the keyword table, or pass `force_model` in the request body.
