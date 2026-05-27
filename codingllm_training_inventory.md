# VxThinking Platform — codingllm Training Dataset Inventory

> Surveyed trees:
> - **Tree 1**: `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/` (208 Go files, confirmed present)
> - **Tree 2**: `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_frontend_ui/app/` (Next.js 15 / TypeScript, confirmed present)

---

## studio.go / studiochat — what the platform generates for "vibe coders"

The Studio subsystem (`services/studio/studio.go`, `services/studio/llm.go`, `services/studio/prompts.go`, `services/studio/studio_features.go`, and the `StudioChat.tsx` / `StudioCodeEditor.tsx` / `StudioShell` frontend) is the primary "vibe-coding" surface: a user opens a workspace in the browser, describes what they want in a chat panel, and the backend materialises complete runnable projects or targeted file diffs. The 3-phase LLM pipeline in `llm.go` works as follows: Phase 1 gathers architectural guidance from a cloud LLM (Anthropic / Gemini / OpenAI / Ollama); Phase 2 runs the enriched prompt through the OpenClaw gateway for final code emission; Phase 3 persists the turn in conversation memory. The Studio can either scaffold entire fresh projects from a single prompt (BUILD mode) or perform minimal targeted edits on an existing codebase (EDIT mode), where only changed or added files are returned so the user's project is never inadvertently overwritten.

**Code-generation patterns found:**

- Generates a complete React SPA (index.html + CDN Babel, `src/App.jsx`, `src/main.jsx`, Tailwind via CDN) from a single user description — "Build an e-commerce store with cart and checkout"
- Emits a Next.js 15 App Router project (page.tsx, layout.tsx, Tailwind v4) via the `nextjs-app` template
- Scaffolds a Python FastAPI REST API (`app.py`, `requirements.txt`) via the `fastapi-api` template
- Generates a Go REST API with Gin (`main.go`, handlers, routes) via the `go-api` template
- Outputs an Expo React Native mobile app (tabs, expo-router, SDK 54) via the `expo-mobile` template
- Writes complete Terraform HCL for AWS VPC + EC2 + RDS via the `terraform-aws` template
- Emits a Docker Compose stack for multi-service local development via the `docker-compose` template
- Produces Kubernetes manifests + Helm chart via the `k8s-deployment` template
- Performs targeted file-diff editing (EDIT mode): "change the background to red" outputs only the one CSS file that contains the background property
- Generates new template files under `templates/<name>/App.jsx` and a minimal route addition to `src/App.jsx` when user requests a new template type
- Emits `deploy.sh`, `docker-compose.yml`, `nginx.conf`, `Dockerfile`, and CI/CD workflow YAML when user asks to deploy

**Key prompts that map to specific code emission:**

| User prompt pattern | Emitted artifact |
|---|---|
| "Build a [description] app" (no existing files) | Complete multi-file project from scratch |
| "EDIT MODE — change [UI element]" | Single patched file (template or CSS) |
| "Add a [page/feature] to this project" | New component file + minimal router change |
| "Create a template for [domain]" | `templates/<name>/App.jsx` + `src/App.jsx` route delta |
| "Deploy this project" | `Dockerfile`, `docker-compose.yml`, `nginx.conf`, CI workflow YAML |
| "Analyze this codebase" | Markdown analysis (no code blocks) via Analyze agent |
| "Write a patch for [X]" | Unified diff only (via Patch agent) |
| "Break this into steps" | JSON step plan (via Planner agent) |

---

## CI/CD code generation

The platform has two code paths for CI/CD YAML generation:

**1. Structured pipeline generator** — `services/cicd/workflow_generator.go`

| Format | Description | Triggering context |
|---|---|---|
| **GitHub Actions** (`GenerateGitHubActionsWorkflow`) | Emits a complete `.github/workflows/<name>.yml` with `actions/checkout@v4`, runtime setup (Node/Python), optional env-var block with `${{ secrets.X }}` references, install step, build step. | Pipeline object has `provider: "github"` set in CI/CD wizard |
| **GitLab CI** (`GenerateGitLabCIWorkflow`) | Emits a `.gitlab-ci.yml` with `stages: [build, deploy]`, runtime image pinning (node:20, python:3.11, golang:1.22), `variables:` block, `only:` branch filter. | Pipeline object has `provider: "gitlab"` |

Both generators accept a `Pipeline` struct (name, runtime, runtime_version, install_command, build_command, start_command, env_vars, branch) and persist the YAML to disk for later streaming.

**2. LLM-driven CI/CD generation** — DevOps agent (`services/ai/agents/devopsagent.go`, AutoDeployAgent)

The DevOps/AutoDeploy agent, when prompted with natural language, emits raw YAML/Groovy/HCL for any of the formats below. It understands the project's runtime from the repository and selects the correct template. These are produced as free-form LLM outputs, not structured generator calls.

| Format | 1-line description | Sample prompt |
|---|---|---|
| **GitHub Actions workflow** | Full CI/CD pipeline YAML for `.github/workflows/` | "Analyze this repo and generate a GitHub Actions pipeline that builds, tests, and pushes to ECR" |
| **GitLab CI YAML** | `.gitlab-ci.yml` with stages, rules, image pinning | "Write a GitLab CI pipeline for my Python FastAPI project" |
| **Jenkinsfile** | Declarative pipeline with agent, stages, steps | "Generate a Jenkinsfile for a Node.js project with Docker build" |
| **Docker Compose** | Multi-service `docker-compose.yml` | "Create a docker-compose for a Next.js app with Postgres and Redis" |
| **Dockerfile** | Multi-stage build, non-root user, HEALTHCHECK | "Generate a production Dockerfile for this Go API" |
| **Kubernetes manifests** | Deployment + Service YAML with resource limits | "Write a Kubernetes deployment for my FastAPI app on port 8000" |
| **Helm chart** | `Chart.yaml` + `templates/` + `values.yaml` | "Scaffold a Helm chart for a stateless Node.js microservice" |
| **Terraform module** | HCL2 with variables, outputs, provider pinning | "Write a Terraform module that provisions an EKS cluster with a node group" |
| **Bash deployment script** | `set -euo pipefail` shell script with SCP/SSH | "Write a deploy.sh that SCPs the dist/ folder to my VM and restarts nginx" |

The CodingAgent (`services/ai/agents/CodingAgent.go`) also emits all formats above via its `language` parameter and knows all aliases (e.g. `"gha"` → `github_actions`, `"tf"` → `terraform`).

---

## Workflow nodes

The platform has a **ReactFlow-based visual workflow DAG builder** (frontend: `app/components/workflow/workflow.tsx`, `workflow_service.ts`; backend executor: `services/workflow/executor.go`). The canvas is an n8n-style drag-and-drop builder. Node types are registered in `executor.go`'s `registerDefaultHandlers()` and visually defined in the frontend's `nodeCategories` array.

**Node categories and types:**

| Category | Node type (executor key) | Description |
|---|---|---|
| **Triggers** | `trigger` / `http_trigger` | HTTP webhook trigger |
| | `schedule_trigger` | Cron-expression schedule trigger |
| | `file_trigger` | Trigger on file system changes |
| | `database_trigger` | Trigger on database row change |
| **Actions** | `action` | Generic action node |
| | `api_call` | HTTP API request |
| | `database_query` | Execute SQL query |
| | `script` / `bash` / `bash_script` | Run Bash script (inline or file) |
| | `python` / `python_script` | Run Python script |
| | `ssh` | SSH remote command |
| | `deploy` | Deployment action |
| | `docker` | Docker container operation |
| | `terraform_exec` | Run `terraform apply` on a module |
| | `script_file` | Upload + execute a local script file |
| **Logic** | `condition` | Conditional branch |
| | `loop` | Iterator over data |
| | `transform` | Data transformation |
| | `filter` | Data filter |
| **Infrastructure (AWS)** | `infrastructure` / `vm` / `ec2` | Generic VM / EC2 provision |
| | `s3` | S3 bucket operations |
| | `lambda` | AWS Lambda function |
| | `rds` | RDS database |
| | `eks` | EKS cluster |
| | `vpc` | VPC provisioning |
| | `route53` | Route 53 DNS |
| | `cloudfront` | CloudFront CDN |
| **Cloudflare** | `cloudflare` / `cloudflare_zone` | Zone management |
| | `cloudflare_dns` | DNS record |
| | `cloudflare_worker` | Workers script |
| | `cloudflare_pages` | Pages project |
| | `cloudflare_waf` | WAF ruleset |
| | `cloudflare_tunnel` | Tunnel |
| | `cloudflare_r2` / `cloudflare_kv` / `cloudflare_d1` | Storage |
| **Integrations** | `slack` | Slack message |
| | `discord` | Discord webhook |
| | `email` | Email send |
| | `github` | GitHub API action |
| | `webhook` | Generic webhook |
| | `integration` | Generic integration |
| **Default** | `default` | Fallback handler |

**Live Terraform generation:** `useTerraformGenerator.ts` maps every canvas node label to a Terraform resource type in real time (`RESOURCE_MAP`), generating HCL as the user drags nodes, covering AWS, Azure, GCP, Cloudflare, Docker, Kubernetes, HashiCorp Vault, and HTTP data sources.

**AI workflow assist:** `WorkflowAgentAssist.tsx` provides a chat bar (modes: Build / Explain / Fix / Ask) that connects to `/api/v3/ai/agent/workflow/chat` (SSE) and generates ReactFlow node+edge JSON that is injected directly into the canvas.

**Key file paths:**
- `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/workflow/executor.go` — all node handler registrations
- `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/workflow/models.go` — WorkflowNode, WorkflowEdge, all activity param structs
- `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_frontend_ui/app/components/workflow/workflow.tsx` — nodeCategories, React node components
- `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_frontend_ui/app/components/workflow/useTerraformGenerator.ts` — RESOURCE_MAP (live HCL generator)

---

## Cloud integrations (Go provisioner)

**AWS** (`services/connectors/aws_deploy_connector.go`, `services/connectors/connectors.go`, `services/connectors/connector_types.go`)

| Operation | Method |
|---|---|
| `ProvisionVM` | EC2 RunInstances via AWS SDK v1 |
| `TerminateVM` | EC2 TerminateInstances |
| `CreateBucket` | S3 CreateBucket |
| `UploadFiles` | S3 PutObject (parallel via errgroup) |
| `EnableStaticHosting` | S3 PutBucketWebsite |
| `DeployStaticSite` | Composite: CreateBucket → UploadFiles → EnableStaticHosting → Route53 CNAME |
| `DeployToVM` | EC2 RunInstances → SCP files → SSH exec |
| `CreateSubdomain` | Route53 ChangeResourceRecordSets |
| `AttachLoadBalancer` | ELBv2 CreateLoadBalancer + TargetGroup + Listener |

**Azure** (`services/connectors/connectors.go`, `services/connectors/azure_keyvault_provider.go`)

| Operation | Method |
|---|---|
| `ProvisionVM` | armcompute VirtualMachines.BeginCreateOrUpdate |
| `CreateVNet` | armnetwork VirtualNetworks |
| Key Vault secrets | Azure SDK for Go (`azidentity`, Key Vault) |
| AKS cluster | azurerm_kubernetes_cluster (via Terraform HCL generation) |

**GCP** (`services/connectors/gcp_deploy_connector.go`)

| Operation | Method |
|---|---|
| `ProvisionVM` | Compute Engine Instances.Insert |
| `DeployCloudRun` | Cloud Run Services.Create (image, port, env vars, IAM public access) |
| `CreateVPC` | Compute Networks |
| GKE | google_container_cluster (via Terraform HCL) |

**Cloudflare** (workflow executor: `handleCloudflareNode`)

- Zone, DNS record, Worker, Pages, WAF, Tunnel, R2, KV, D1 provisioning via Terraform provider nodes in the workflow engine.

**On-premise** (`services/onpremterraformcloud/onpremterraformcloud.go`)

- Terraform Cloud / on-prem workspace management, state backend configuration.

---

## Third-party integrations

| Integration | Code path(s) | What is wired |
|---|---|---|
| **GitHub** | `services/agentcontrol/github.go`, `services/githubactions/githubactions.go`, `services/studio/studio_git.go`, `services/studio/agents/GitAgent.go` | OAuth, repo listing, push, PR creation, GitHub Actions YAML push via API |
| **GitLab** | `workflow.tsx` icons, `StudioPushRepoBrowser.tsx`, `Integrations.tsx` | OAuth connect, repo list, MR creation, GitLab CI YAML push |
| **Bitbucket** | `workflow.tsx` (FaBitbucket icon, Bitbucket webhook node in RESOURCE_MAP), `Integrations.tsx` | Webhook trigger, pipeline trigger via API |
| **Slack** | `services/notifications/notifications.go`, workflow `handleSlackNode` | Deployment notifications, workflow step messages |
| **Discord** | Workflow `handleDiscordNode` | Webhook notifications |
| **Email (SES / SMTP)** | Workflow `handleEmailNode`, SES resource in Terraform generator | Transactional email step, AWS SES identity provisioning |
| **Stripe** | `Integrations.tsx` (id: 'stripe'), `services/billings/billings.go` | Payment processing integration card, billing service |
| **Jira** | `workflow.tsx` (FaJira icon, node type) | Workflow node (not yet a full API integration, icon-level) |
| **Trello** | `workflow.tsx` (FaTrello icon) | Workflow node (icon-level) |
| **HashiCorp Vault** | `config/vault.go`, `services/neocplus/guardian.go` | Secrets management, workspace credential store |
| **Anthropic Claude** | `config/vallm_client.go`, `Integrations.tsx` | LLM backend, API key integration card |
| **OpenAI** | `services/ai/agents/CodingAgent.go`, `Integrations.tsx` | LLM backend, API key integration card |
| **Google Gemini** | `services/studio/llm.go`, `Integrations.tsx` | LLM backend Phase 1 knowledge gathering |
| **Ollama** | `config/vallm_client.go`, model catalog | Local model backend |
| **HuggingFace** | `agent_model_catalog.ts` | Local model backend (TinyLlama, Qwen, Phi, Gemma) |
| **Meta Llama** | `agent_model_catalog.ts` | Open-source model backend |
| **Google OAuth** | `Integrations.tsx` (oauthProvider: 'google') | GCP integration OAuth |
| **Microsoft (Azure)** | `Integrations.tsx` (oauthProvider: 'microsoft') | Azure DevOps OAuth |

---

## Code-emitting agents

### CodingAgent
**Location:** `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/ai/agents/CodingAgent.go`

**What it produces:** Single-shot or ReAct-loop generation of any artifact in the `CodingLanguages` catalog: Python, TypeScript, JavaScript, Go, Rust, Java, Bash, SQL, C#, HTML, CSS, Markdown, Terraform/HCL, GitHub Actions YAML, GitLab CI YAML, Jenkinsfile, Dockerfile, docker-compose YAML, nginx config, Kubernetes manifests, Helm charts, YAML, TOML, JSON, dotenv.

**Modes:**
- `Generate(ctx, query, language)` — single-shot prompt → fenced code block (fast path)
- `Run(ctx, prompt)` — ReAct loop with file tools (`read_file`, `write_file`, `list_dir`, `find_files`, `grep`, `validate_yaml`, `lint_dockerfile`, `validate_json`) — used when the user says "scan this folder and add unit tests"

**Routes:** `POST /api/v2/agents/coding/generate`, `POST /api/v2/agents/coding/agent`, `POST /api/v2/agents/coding/agent/stream`, `POST /api/v2/agents/coding/tool`, `GET /api/v2/agents/coding/tools`

**Sample prompts:**
- "Write a Dockerfile for a Python FastAPI app on port 8000"
- "Generate a GitHub Actions workflow that builds and pushes a Docker image to ECR"
- "Create a Terraform module for an EKS cluster with a managed node group"
- "Write a multi-stage Go Dockerfile with distroless final image"
- "Scaffold a NestJS REST API with TypeScript and Prisma ORM"

---

### DevOps Agent (ServiceChat + AutoDeployAgent)
**Location:** `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/ai/agents/devopsagent.go`, `services/studio/agents/AutoDeployAgent.go`

**What it produces:** JSON action blocks that the system executes via SCP+SSH (scripts) or terraform apply (HCL), plus emitted files (Dockerfile, CI YAML, deploy scripts, nginx configs). The LLM writes the files; the platform executes them against a VM.

**Sub-agents (AutoDeployAgent):**
- `GitSubAgent` — git operations, PR creation
- `VMSubAgent` — VM status, start, stop, SSH
- `DockerSubAgent` — container lifecycle, logs, build, compose
- `PipelineSubAgent` — CI/CD pipeline generation
- `AnalysisSubAgent` — code review, infra assessment

**Routes:** `POST /api/v2/tenant/services/chat`, `POST /api/v2/agents/devops/run` (SSE), CLI: `vxcli agent devops`

**Sample prompts:**
- "Deploy my Go app to Docker and push the code to GitHub"
- "Analyze this repo and generate a GitHub Actions CI pipeline"
- "Restart all stopped containers and show me the logs"
- "Create a deployment plan for staging on AWS"
- "Provision an S3 bucket and enable static website hosting"

---

### GitAgent
**Location:** `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/studio/agents/GitAgent.go`

**What it produces:** Git operations driven by natural language; also generates smart commit messages from diffs, branch names following conventional commit conventions, and PR/MR bodies. Does not produce source code artifacts directly — operates the Git tool suite.

**Routes:** `POST /api/v2/agents/git/run`, CLI: `vxcli agent git`

**Sample prompts:**
- "Stage all files and write a smart conventional commit message"
- "Create a feature branch for dark-mode support and push it"
- "Open a PR from feat/auth to main with a summary of changes"

---

### ParallelAgent
**Location:** `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/studio/agents/ParallelAgent.go`

**What it produces:** Fan-out execution where multiple sub-agents run concurrently (each with its own LLM provider), then a synthesizer aggregates results. Used for multi-perspective reviews, e.g. security + cost + compliance review of the same Terraform plan.

**Built-in presets (from CLI flags):**
- `infra-review` — security, cost, compliance sub-agents in parallel
- `pr-review` — multiple reviewer perspectives on a PR diff
- Custom: `--agents "security:anthropic,cost:openai,compliance:gemini"`

**Routes:** CLI: `vxcli agent parallel --preset infra-review --prompt "..."`

---

### Studio Build/Coding/Planner/Patch/Analyze agents (prompt-only, no separate process)
**Location:** `/mnt/c/Users/joelwembo/Desktop/EmergentCloud/financedapp1/va_golang_infra_provisionner/services/studio/prompts.go`

These are system prompt variants injected into the 3-phase pipeline:

| Agent ID | Produces |
|---|---|
| `build` | Complete multi-file apps or targeted file edits (vibecoding style) |
| `coding` | Tool-driven Go file patches (unified diffs only) |
| `chat` | Explanations, no file modification |
| `planner` | JSON step-plan for Coding Agent to execute |
| `patch` | Minimal unified diff, no prose |
| `analyze` | Rich markdown analysis, no code blocks |

**Routes:** `POST /api/v2/studio/generate` (body: `{agent: "build"|"coding"|..., prompt: "..."}`)

---

## Frontend code-editor / chat surface

### Monaco Editor
- **Component:** `app/features/studio/components/StudioCodeEditor.tsx`
- **Library:** `@monaco-editor/react` (dynamically imported, SSR disabled)
- **Custom theme:** VSCode Modern Dark (`app/components/editors/monaco/vscodeModernDarkTheme.ts`)
- **Language registration:** `app/components/editors/monaco/registerLanguages.ts` — covers JS, TS, TSX, HTML, CSS, SCSS, JSON, YAML, Python, Go, Rust, Java, Dockerfile, Terraform, SQL, Markdown, Bash, and more (mapped from file extension via `EXT_TO_LANGUAGE`)
- **Split view:** `StudioCodeEditor` supports side-by-side file comparison via `projectFiles` prop + `Columns2` toggle
- **Editor also appears in:** `WorkflowCodeEditor.tsx` (workflow YAML/JSON editor), `AIGeneratorView.tsx` (code generation preview)

### Chat / AI Assistant surfaces
- **`AIAssistant.tsx`** — Full-featured multi-agent chat (`app/components/ai/AIAssistant.tsx`). Modes: fullscreen, compact, normal. Supports: agent selection dropdown (25+ agents), model selection dropdown, file uploads, code highlighting in Monaco, draggable window, SSE streaming, session history, voice mode placeholder.
- **`StudioChat.tsx`** — Studio-embedded chat panel (`app/features/studio/components/StudioChat.tsx`). Wired to `POST /api/v2/studio/agent/chat` (SSE). Shows STUDIO_AGENTS subset; displays file change summaries from Build agent; integrates with StudioCodeEditor for "Apply" of emitted file blocks.
- **`AgentModeComponent.tsx`** — Agentic coding mode in the main chat: shows run phases (planning → thinking → coding → git → pr → done), file change diffs, branch/PR links.
- **`WorkflowAgentAssist.tsx`** — Chat bar on the workflow canvas (modes: Build / Explain / Fix / Ask). Injects generated ReactFlow nodes directly into the canvas.
- **`AIGeneratorView.tsx`** — Standalone code generator UI (`app/components/ai/AIGeneratorView.tsx`). Language selector (Python, JS, TS, Java, C#, Go, Rust, SQL, Terraform, Dockerfile), prompt templates, Monaco preview, copy/download/insert actions. Calls `POST /api/v3/ai/agent/generate`.
- **`CloudShell.tsx`** — Browser-based cloud shell, embedded in AI Assistant sidebar.

---

## "Skills" the codingllm should know about

### Dockerfile / Container skills
- Generate a single-stage Dockerfile for a Python Flask app (python:3.12-slim, pip install, gunicorn CMD)
- Generate a multi-stage Dockerfile for a Go API (golang:1.22 builder → distroless/static final)
- Generate a multi-stage Dockerfile for a Node.js app (node:20-alpine builder → node:20-alpine runtime, non-root user)
- Write a Dockerfile for a FastAPI app with uvicorn, non-root USER, HEALTHCHECK
- Write a Dockerfile for a Next.js SSR app with standalone output mode
- Generate a Dockerfile for a Rust binary using cargo-chef for layer caching
- Pin a Dockerfile base image and add a HEALTHCHECK curl probe
- Add a `.dockerignore` file for a Node.js / Python / Go project

### Docker Compose skills
- Generate a `docker-compose.yml` for a Next.js + Postgres + Redis stack
- Generate a `docker-compose.yml` for a FastAPI + Celery + Redis + Postgres stack
- Write a Compose file with named volumes, a custom bridge network, and health checks
- Add environment variable parametrisation (`${VAR:-default}`) to a Compose file
- Write a Compose override file for local development (bind-mount source code, hot reload)

### GitHub Actions skills
- Write a GitHub Actions workflow that builds and tests a Node.js project on push to main
- Generate a GHA workflow that builds a Docker image and pushes it to Amazon ECR
- Write a GHA workflow that runs Terraform plan on PR and apply on merge to main
- Generate a GHA workflow for Go: lint (golangci-lint), test, build binary, upload artifact
- Write a GHA workflow that runs pytest with coverage, uploads to Codecov
- Generate a GHA workflow with matrix strategy for Node 18/20 and Ubuntu/macOS
- Write a GHA workflow that deploys a Next.js app to Vercel on push
- Generate a GHA workflow for semantic release and npm publish

### GitLab CI skills
- Write a `.gitlab-ci.yml` with stages: build, test, deploy for a Python project
- Generate a GitLab CI pipeline with Docker-in-Docker image build and push to GitLab Registry
- Write a GitLab CI pipeline for a Go microservice with caching
- Generate a GitLab CI pipeline with environment-specific deploy rules (staging vs production)

### Terraform / IaC skills
- Write a Terraform module for an AWS VPC with public/private subnets across 3 AZs
- Generate a Terraform module for an EC2 auto-scaling group behind an Application Load Balancer
- Write a Terraform module for an EKS cluster with a managed node group and IRSA
- Generate a Terraform module for an RDS Postgres instance with multi-AZ and parameter group
- Write a Terraform module for S3 static website hosting with CloudFront and ACM certificate
- Generate a Terraform module for Lambda + API Gateway with IAM role and CloudWatch log group
- Write a Terraform resource for an Azure AKS cluster with system and user node pools
- Generate a Terraform resource for a GCP Cloud Run service with IAM public access
- Write a Terraform module for Cloudflare DNS records, Workers, and R2 bucket
- Write a `variables.tf` + `outputs.tf` + `main.tf` split for any Terraform module
- Generate a `.tfvars` file for a production environment
- Write a Terraform remote state backend configuration for S3 + DynamoDB lock table

### Kubernetes / Helm skills
- Generate a Kubernetes Deployment manifest with resource requests/limits, liveness/readiness probes
- Write a Kubernetes Service (ClusterIP / NodePort / LoadBalancer) for a web app
- Generate a Kubernetes ConfigMap and Secret (base64 encoded)
- Write a Kubernetes Ingress with TLS annotation for cert-manager
- Generate a Kubernetes HorizontalPodAutoscaler for a Deployment
- Scaffold a Helm chart (Chart.yaml, values.yaml, deployment.yaml, service.yaml, ingress.yaml)
- Write a Helm values override file for a production environment
- Generate a Kubernetes NetworkPolicy that restricts egress to a specific namespace

### Application scaffolding skills
- Scaffold a FastAPI app with Pydantic v2 models, async endpoints, and pytest setup
- Scaffold a Django REST Framework API with custom serializers and viewsets
- Generate a React functional component with TypeScript, hooks, and Tailwind CSS
- Scaffold a Next.js 15 App Router page with `generateMetadata` and a Server Component
- Scaffold a Go HTTP API with Gin, middleware (logging, auth), and structured error responses
- Scaffold a NestJS module with controller, service, DTO, and Prisma entity
- Generate a Python CLI tool with Click, logging, and a Dockerfile
- Scaffold an Express.js REST API with TypeScript, Zod validation, and Jest tests
- Generate a Rust Actix-web REST API with error handling and serde models

### Configuration / DevOps file skills
- Write an nginx virtual host config with TLS termination, gzip, and proxy_pass to a container
- Generate a `.env.example` file with all required environment variables documented
- Write a `Makefile` for a Go project (build, test, lint, docker-build, docker-push targets)
- Generate a `pyproject.toml` for a Python package with ruff, mypy, and pytest
- Write a `package.json` with scripts for a Next.js project
- Generate a `renovatebot.json` config for automated dependency updates
- Write a `pre-commit` configuration with hooks for Python (ruff, mypy) or Go (gofmt, golangci-lint)

### SQL / Database skills
- Write a PostgreSQL schema with CTEs, foreign keys, and indexes for a SaaS app
- Generate a Django migration script for adding a new model with indexes
- Write a SQL migration that adds a nullable column and back-fills it
- Generate a SQLAlchemy model with async session and relationship declarations

### Security / IaC hardening skills
- Add a non-root USER to any Dockerfile
- Write an AWS Security Group Terraform resource with least-privilege ingress rules
- Generate a Kubernetes Pod Security Context with runAsNonRoot and readOnlyRootFilesystem
- Write a GitHub Actions OIDC trust policy for keyless AWS authentication

---

## Sample prompt → expected output pairs (for training rows)

These 40 pairs are formatted as `(user_prompt, expected_artifact_description)`. The "expected artifact" describes what the model should emit — not the actual code.

1. ("Write a Dockerfile for a Python FastAPI app", "Multi-stage Dockerfile: python:3.12-slim base, pip install -r requirements.txt, non-root USER, EXPOSE 8000, CMD uvicorn main:app --host 0.0.0.0")
2. ("Write a multi-stage Go Dockerfile with distroless final image", "Two-stage Dockerfile: golang:1.22-alpine builder, copies go.mod/go.sum, runs go build, final FROM gcr.io/distroless/static-debian12, copies binary, non-root USER 65534")
3. ("Generate a docker-compose.yml for Next.js + Postgres + Redis", "Compose v3 file: web service (build: .), db service (image: postgres:15, named volume, env vars), redis service (image: redis:7-alpine), custom bridge network, healthchecks on db and redis")
4. ("Write a GitHub Actions workflow that builds and pushes to ECR", "YAML workflow: checkout, configure-aws-credentials@v4, login-to-amazon-ecr, docker build/tag/push, uses ${{ secrets.AWS_ACCESS_KEY_ID }} and ${{ secrets.AWS_SECRET_ACCESS_KEY }}")
5. ("Generate a GitHub Actions workflow for a Go project with lint and test", "Workflow: actions/setup-go@v5 with go-version 1.22, run golangci-lint-action@v4, go test ./... with -race flag, build artifact upload")
6. ("Write a GitLab CI pipeline for a FastAPI project", ".gitlab-ci.yml: stages [build, test, deploy], image python:3.11, pip install, pytest, deploy stage with SSH, only on main branch")
7. ("Generate a Jenkinsfile for a Node.js Docker build", "Declarative pipeline: agent any, stages [Checkout, Build Docker Image, Push to Registry, Deploy], uses withCredentials for registry creds, sh docker build/push commands")
8. ("Write a Terraform module for an AWS VPC with public and private subnets", "main.tf: aws_vpc, aws_subnet (2 public + 2 private across 2 AZs), aws_internet_gateway, aws_nat_gateway, aws_route_table + association, variables.tf with vpc_cidr/environment, outputs.tf with vpc_id/subnet_ids")
9. ("Create a Terraform module for an EKS cluster", "main.tf: aws_eks_cluster with role_arn, aws_eks_node_group with instance_types and scaling_config, aws_iam_role + attachment for cluster and nodes, variables for cluster_name/node_instance_type/desired_size")
10. ("Write a Terraform resource for S3 static website hosting with CloudFront", "aws_s3_bucket, aws_s3_bucket_website_configuration, aws_cloudfront_distribution with S3 origin, aws_acm_certificate (us-east-1), aws_route53_record CNAME, outputs website_url")
11. ("Generate a Terraform module for an RDS Postgres instance", "aws_db_instance with engine postgres, instance_class db.t3.micro, multi_az = true, aws_db_subnet_group, aws_security_group, random_password for db password, output endpoint")
12. ("Scaffold a FastAPI app with Pydantic v2 and pytest", "app/main.py with lifespan, routers; app/models.py with BaseModel; app/schemas.py; requirements.txt (fastapi, uvicorn, pydantic>=2, pytest, httpx); tests/test_main.py with pytest-asyncio fixture")
13. ("Generate a Next.js 15 App Router page with metadata and a server component", "app/page.tsx as async Server Component, generateMetadata export, fetch data with cache: 'force-cache', TypeScript interfaces, Tailwind CSS layout")
14. ("Scaffold a Go REST API with Gin middleware", "main.go with gin.New(), custom Logger and Recovery middleware, routes grouped under /api/v1, handlers in handlers/ package, structured JSON error responses, config from env with godotenv")
15. ("Write a Kubernetes Deployment with liveness and readiness probes", "Deployment YAML: apps/v1, 3 replicas, resource requests/limits, livenessProbe httpGet /health, readinessProbe httpGet /ready, imagePullPolicy Always, env from ConfigMap and Secret refs")
16. ("Generate a Helm chart for a stateless Node.js microservice", "Chart.yaml, values.yaml (replicaCount, image.repository/tag, service.type/port, ingress.enabled), templates/deployment.yaml, templates/service.yaml, templates/ingress.yaml with TLS section")
17. ("Write an nginx config for a React SPA with TLS", "server block: listen 443 ssl, ssl_certificate paths, gzip on, try_files $uri /index.html for SPA routing, proxy_pass for /api/ to backend, security headers (X-Frame-Options, HSTS)")
18. ("Generate a .github/workflows/terraform.yml that plans on PR and applies on merge", "Workflow with two jobs: plan (runs on: pull_request, terraform plan -out=tfplan, uploads plan artifact) and apply (runs on: push to main, downloads artifact, terraform apply)")
19. ("Write a Dockerfile for a Node.js app with a non-root user and health check", "Dockerfile: FROM node:20-alpine, WORKDIR /app, COPY package*.json, npm ci --only=production, COPY . ., RUN addgroup/adduser nonroot, USER nonroot, HEALTHCHECK CMD wget -qO- localhost:3000/health")
20. ("Generate a Python Django REST Framework API with serializers and viewsets", "models.py, serializers.py with ModelSerializer, views.py with ModelViewSet, urls.py with DefaultRouter, settings.py snippets for DRF, requirements.txt")
21. ("Write a Kubernetes Ingress with cert-manager TLS", "Ingress YAML: annotations kubernetes.io/ingress.class nginx, cert-manager.io/cluster-issuer letsencrypt-prod, tls block with secretName, rules with host and path")
22. ("Create a GitHub Actions matrix workflow for Node 18 and 20", "Workflow with strategy.matrix.node-version: [18, 20], actions/setup-node@v4 with node-version: ${{ matrix.node-version }}, npm ci, npm test")
23. ("Write a Terraform backend configuration for S3 + DynamoDB state locking", "terraform { backend \"s3\" { bucket, key, region, dynamodb_table, encrypt = true } }, plus provider.tf with version constraints")
24. ("Generate a NestJS module with controller, service, and Prisma entity", "src/users/users.module.ts, users.controller.ts (CRUD routes, DTOs), users.service.ts (PrismaService injection), create-user.dto.ts with class-validator, prisma/schema.prisma User model")
25. ("Write a bash deployment script that SCPs files to a VM and restarts nginx", "#!/bin/bash set -euo pipefail, rsync or scp dist/ to remote, ssh remote 'sudo systemctl restart nginx', error handling, progress messages")
26. ("Generate a Kubernetes HorizontalPodAutoscaler for a web deployment", "HPA YAML: autoscaling/v2, scaleTargetRef to Deployment, minReplicas 2 maxReplicas 10, metrics CPU averageUtilization 70, memory averageUtilization 80")
27. ("Write a pre-commit config for a Python project with ruff and mypy", ".pre-commit-config.yaml: repos for pre-commit-hooks (trailing-whitespace, end-of-file-fixer), ruff-pre-commit (ruff + ruff-format), mypy with --strict")
28. ("Generate a GCP Cloud Run Terraform resource", "google_cloud_run_service with template.spec.containers image/env/resources, traffic 100% latest, google_cloud_run_service_iam_member for allUsers, output service_url")
29. ("Write a React component with TypeScript and Tailwind for a data table", "Functional component with typed props interface, useState for sorting/filtering, TailwindCSS table classes, responsive overflow-x-auto wrapper, empty state")
30. ("Generate a Renovate bot config for a monorepo", "renovate.json with $schema, extends base:js-app, packageRules for grouping, schedule, prConcurrentLimit, labels, automerge for patch/minor devDependencies")
31. ("Write a docker-compose for a Celery + Redis + FastAPI stack", "Services: api (build, depends_on redis), worker (same image, command celery -A app.worker worker), beat (celery beat), redis (redis:7-alpine), shared network, .env file reference")
32. ("Generate a Terraform CloudFront distribution for a private S3 bucket", "aws_cloudfront_origin_access_identity, aws_s3_bucket_policy with OAI principal, aws_cloudfront_distribution with s3_origin_config, HTTPS redirect, price_class PriceClass_100")
33. ("Scaffold a Rust Actix-web API with serde and error handling", "main.rs with HttpServer, routes module, handlers with web::Json extractors, AppError enum implementing ResponseError, Cargo.toml with actix-web/serde/tokio dependencies")
34. ("Write a GitHub Actions workflow for semantic-release and npm publish", "Workflow: checkout with fetch-depth 0, setup Node, npm ci, npx semantic-release — uses NPM_TOKEN and GH_TOKEN secrets, runs only on main")
35. ("Generate a Kubernetes NetworkPolicy that isolates a namespace", "NetworkPolicy YAML: podSelector {}, policyTypes [Ingress, Egress], ingress from namespaceSelector matchLabels, egress to port 443 and DNS port 53")
36. ("Write a pyproject.toml for a Python package with ruff and mypy", "[tool.ruff] with select rules, [tool.mypy] with strict = true, [tool.pytest.ini_options] testpaths, [project] with version and dependencies, [build-system] using hatchling")
37. ("Generate an Azure AKS Terraform module", "azurerm_kubernetes_cluster with default_node_pool (vm_size, node_count, os_disk_size_gb), identity SystemAssigned, network_profile kubenet, azurerm_resource_group, outputs kube_config")
38. ("Write a Makefile for a Go project", "Targets: build (go build -ldflags), test (go test -race ./...), lint (golangci-lint run), docker-build (docker build -t), docker-push, clean, .PHONY declaration")
39. ("Generate a .env.example file for a SaaS app", "All required env vars documented with inline comments: DATABASE_URL, REDIS_URL, JWT_SECRET, STRIPE_SECRET_KEY, ANTHROPIC_API_KEY, S3_BUCKET, AWS_REGION, PORT — no real values")
40. ("Write a Terraform module for AWS Lambda + API Gateway v2", "aws_iam_role + policy for Lambda, aws_lambda_function (filename, runtime python3.12, handler), aws_apigatewayv2_api (HTTP), aws_apigatewayv2_integration, aws_apigatewayv2_route, aws_lambda_permission, output invoke_url")

---

*Generated 2026-04-26 by survey of va_golang_infra_provisionner (208 Go files) and va_frontend_ui/app (Next.js 15 TypeScript).*
