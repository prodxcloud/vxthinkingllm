"""
API Routes for VaLLM
Four endpoints: /query, /developer, /terminal, /query/websearch
"""

from fastapi import APIRouter, HTTPException, Request, Body
import logging
import time
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from collections import Counter
import json
import numpy as np
import torch
from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import IsolationForest
import xgboost as xgb

# Import web search functionality
try:
    from .web_search import CloudDevOpsWebSearch
except ImportError:
    from web_search import CloudDevOpsWebSearch

router = APIRouter()
router_v3 = APIRouter()
logger = logging.getLogger("vallm")


def _summarize_context(results: list, max_items: int = 3, preview_chars: int = 180) -> str:
    if not results:
        return "no_results"
    parts = []
    for r in results[:max_items]:
        doc = (r.get("document") or "").replace("\n", " ").strip()
        if len(doc) > preview_chars:
            doc = f"{doc[:preview_chars]}..."
        meta = r.get("metadata") or {}
        doc_type = meta.get("type", "unknown") if isinstance(meta, dict) else "unknown"
        score = r.get("score", 0.0)
        parts.append(f"[{doc_type}] score={score:.4f} doc='{doc}'")
    return " | ".join(parts)


def _build_terraform_example(query: str) -> str:
    """Return a full Terraform example based on the query intent."""
    q = (query or "").lower()
    wants_vpc = "vpc" in q or "subnet" in q or "flow log" in q
    wants_private_dns = "private dns" in q or "private dns namespace" in q
    wants_kms = "kms" in q or "encryption" in q

    if wants_vpc:
        dns_namespace_block = ""
        if wants_private_dns:
            dns_namespace_block = """
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "svc.prod.internal"
  vpc  = aws_vpc.main.id
  description = "Private DNS namespace for internal services"
}
""".strip()

        kms_blocks = ""
        log_kms_id = ""
        if wants_kms:
            kms_blocks = """
resource "aws_kms_key" "logs" {
  description             = "KMS key for VPC flow logs"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}
""".strip()
            log_kms_id = "  kms_key_id = aws_kms_key.logs.arn\n"

        return f"""
provider "aws" {{
  region = "us-east-1"
}}

{kms_blocks}

resource "aws_vpc" "main" {{
  cidr_block           = "10.50.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {{
    Name        = "prod-vpc"
    Environment = "Production"
    Compliance  = "SOC2"
  }}
}}

resource "aws_subnet" "private_a" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.50.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = false
}}

resource "aws_cloudwatch_log_group" "vpc_flow" {{
  name = "/vpc/flow-logs"
{log_kms_id}  retention_in_days = 30
}}

resource "aws_iam_role" "vpc_flow" {{
  name = "vpc-flow-logs-role"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Effect = "Allow"
      Principal = {{ Service = "vpc-flow-logs.amazonaws.com" }}
      Action = "sts:AssumeRole"
    }}]
  }})
}}

resource "aws_iam_role_policy" "vpc_flow" {{
  name = "vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow.id
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Resource = "*"
    }}]
  }})
}}

resource "aws_flow_log" "vpc" {{
  vpc_id               = aws_vpc.main.id
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.vpc_flow.arn
  iam_role_arn         = aws_iam_role.vpc_flow.arn
  traffic_type         = "ALL"
}}

{dns_namespace_block}
""".strip()

    return """
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "example-app-bucket"

  tags = {
    Environment = "Production"
    Owner       = "platform-team"
  }
}
""".strip()


class QueryRequest(BaseModel):
    """Query endpoint request model"""
    query: str
    top_k: Optional[int] = 5
    filter_type: Optional[str] = None
    include_reasoning: Optional[bool] = True


class DeveloperRequest(BaseModel):
    """Developer endpoint request model"""
    query: str
    context: Optional[Dict[str, Any]] = None
    include_code: Optional[bool] = True
    include_reasoning: Optional[bool] = True


class TerminalRequest(BaseModel):
    """Terminal endpoint request model"""
    command: str
    context: Optional[Dict[str, Any]] = None
    include_explanation: Optional[bool] = True


class V3QueryRequest(BaseModel):
    """V3 query endpoint request model with cloud/devops incident patterns"""
    query: str
    top_k: Optional[int] = 10
    include_reasoning: Optional[bool] = True
    focus: Optional[str] = "cloud_devops"
    enable_web_search: Optional[bool] = True  # Enable web search for incident context
    domain_focus: Optional[str] = "devops"  # Domain for web search


class WebSearchRequest(BaseModel):
    """Web search query request model"""
    query: str
    domain_focus: Optional[str] = "cloud"  # cloud, devops, networking, observability, programming, it_support
    use_deep_search: Optional[bool] = False
    combine_with_rag: Optional[bool] = True
    top_k: Optional[int] = 5


CLOUD_DEVOPS_KEYWORDS = {
    "aws", "azure", "gcp", "kubernetes", "eks", "aks", "gke",
    "vpc", "iam", "ec2", "s3", "rds", "cloud", "container",
    "docker", "k8s", "cicd", "ci", "cd", "terraform", "ansible",
    "devops", "network", "security", "vpn", "dns", "loadbalancer",
}


def _normalize_incident_meta(meta: Dict[str, Any]) -> Dict[str, str]:
    raw = meta.get("raw") or meta.get("raw_data") or {}
    return {
        "incident_id": str(raw.get("incident_id", "")),
        "severity": str(raw.get("severity", "")).lower(),
        "category": str(raw.get("category", "")).lower(),
        "service": str(raw.get("service", "")).lower(),
        "error_code": str(raw.get("error_code", "")).lower(),
        "tags": str(raw.get("tags", "")).lower(),
        "timestamp": str(raw.get("timestamp", "")),
    }


def _is_cloud_devops_incident(incident: Dict[str, str]) -> bool:
    haystack = " ".join(
        [
            incident.get("category", ""),
            incident.get("service", ""),
            incident.get("tags", ""),
            incident.get("error_code", ""),
        ]
    )
    return any(keyword in haystack for keyword in CLOUD_DEVOPS_KEYWORDS)


def _severity_to_score(severity: str) -> float:
    mapping = {
        "critical": 1.0,
        "high": 0.75,
        "medium": 0.5,
        "low": 0.25,
    }
    return mapping.get(severity, 0.0)


def _compute_query_similarity(
    vector_store,
    query: str,
    incidents: List[Dict[str, Any]]
) -> List[float]:
    if not incidents:
        return []
    if not getattr(vector_store, "model", None):
        return [0.0 for _ in incidents]

    documents = [item.get("document", "") for item in incidents]
    embeddings = vector_store.model.encode(documents, convert_to_numpy=True)
    query_embedding = vector_store.model.encode([query], convert_to_numpy=True)[0]

    doc_t = torch.tensor(embeddings, dtype=torch.float32)
    query_t = torch.tensor(query_embedding, dtype=torch.float32)
    doc_norm = torch.nn.functional.normalize(doc_t, dim=1)
    query_norm = torch.nn.functional.normalize(query_t, dim=0)
    similarities = torch.matmul(doc_norm, query_norm).cpu().numpy().tolist()
    return [float(s) for s in similarities]


def analyze_unusual_incident_patterns(incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized = []
    for item in incidents:
        meta = _normalize_incident_meta(item.get("metadata", {}))
        normalized.append(meta)

    if not normalized:
        return {
            "unusual_incidents": [],
            "metrics": {
                "total_incidents": 0,
                "total_candidates": 0,
                "unusual_count": 0,
                "unusual_rate": 0.0,
                "unique_categories": 0,
                "unique_services": 0,
                "unique_error_codes": 0,
            },
            "top_patterns": [],
        }

    category_counts = Counter(i["category"] for i in normalized if i["category"])
    service_counts = Counter(i["service"] for i in normalized if i["service"])
    error_counts = Counter(i["error_code"] for i in normalized if i["error_code"])

    unusual = []
    for inc in normalized:
        signals = []
        if inc["severity"] in {"critical", "high"}:
            signals.append("high_severity")
        if inc["category"] and category_counts[inc["category"]] == 1:
            signals.append("rare_category")
        if inc["service"] and service_counts[inc["service"]] == 1:
            signals.append("rare_service")
        if inc["error_code"] and error_counts[inc["error_code"]] == 1:
            signals.append("rare_error_code")
        if _is_cloud_devops_incident(inc):
            signals.append("cloud_devops_signal")

        if signals:
            unusual.append(
                {
                    "incident_id": inc.get("incident_id"),
                    "severity": inc.get("severity"),
                    "category": inc.get("category"),
                    "service": inc.get("service"),
                    "error_code": inc.get("error_code"),
                    "timestamp": inc.get("timestamp"),
                    "signals": signals,
                }
            )

    metrics = {
        "total_incidents": len(normalized),
        "total_candidates": len(normalized),
        "unusual_count": len(unusual),
        "unusual_rate": round(len(unusual) / max(len(normalized), 1), 3),
        "unique_categories": len(category_counts),
        "unique_services": len(service_counts),
        "unique_error_codes": len(error_counts),
    }

    top_patterns = [
        {
            "pattern": "top_categories",
            "values": category_counts.most_common(3),
        },
        {
            "pattern": "top_services",
            "values": service_counts.most_common(3),
        },
        {
            "pattern": "top_error_codes",
            "values": error_counts.most_common(3),
        },
    ]

    return {
        "unusual_incidents": unusual,
        "metrics": metrics,
        "top_patterns": top_patterns,
    }


def analyze_unusual_incident_patterns_v3(
    vector_store,
    query: str,
    incidents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    normalized = []
    for item in incidents:
        meta = _normalize_incident_meta(item.get("metadata", {}))
        normalized.append(meta)

    if not normalized:
        return {
            "unusual_incidents": [],
            "metrics": {
                "total_incidents": 0,
                "total_candidates": 0,
                "unusual_count": 0,
                "unusual_rate": 0.0,
                "unique_categories": 0,
                "unique_services": 0,
                "unique_error_codes": 0,
            },
            "top_patterns": [],
            "success_metrics": {
                "avg_anomaly_score": 0.0,
                "avg_xgb_residual": 0.0,
                "avg_query_similarity": 0.0,
            },
        }

    category_counts = Counter(i["category"] for i in normalized if i["category"])
    service_counts = Counter(i["service"] for i in normalized if i["service"])
    error_counts = Counter(i["error_code"] for i in normalized if i["error_code"])

    query_similarities = _compute_query_similarity(vector_store, query, incidents)

    categorical_dicts = []
    numeric_features = []
    severity_scores = []
    for idx, inc in enumerate(normalized):
        categorical_dicts.append(
            {
                "category": inc.get("category", ""),
                "service": inc.get("service", ""),
                "error_code": inc.get("error_code", ""),
            }
        )
        severity_score = _severity_to_score(inc.get("severity", ""))
        severity_scores.append(severity_score)
        numeric_features.append(
            [
                severity_score,
                float(category_counts.get(inc.get("category", ""), 0)),
                float(service_counts.get(inc.get("service", ""), 0)),
                float(error_counts.get(inc.get("error_code", ""), 0)),
                float(query_similarities[idx]) if idx < len(query_similarities) else 0.0,
            ]
        )

    vectorizer = DictVectorizer(sparse=False)
    cat_matrix = vectorizer.fit_transform(categorical_dicts)
    feature_matrix = np.hstack([np.array(numeric_features, dtype=np.float32), cat_matrix])

    iso_forest = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=42,
    )
    iso_scores = -iso_forest.fit_predict(feature_matrix)
    anomaly_scores = iso_forest.decision_function(feature_matrix)

    xgb_model = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.1,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=1,
    )
    xgb_model.fit(feature_matrix, np.array(severity_scores, dtype=np.float32))
    xgb_pred = xgb_model.predict(feature_matrix)
    xgb_residuals = np.abs(xgb_pred - np.array(severity_scores, dtype=np.float32))

    unusual = []
    for idx, inc in enumerate(normalized):
        signals = []
        if inc["severity"] in {"critical", "high"}:
            signals.append("high_severity")
        if inc["category"] and category_counts[inc["category"]] == 1:
            signals.append("rare_category")
        if inc["service"] and service_counts[inc["service"]] == 1:
            signals.append("rare_service")
        if inc["error_code"] and error_counts[inc["error_code"]] == 1:
            signals.append("rare_error_code")
        if _is_cloud_devops_incident(inc):
            signals.append("cloud_devops_signal")
        if iso_scores[idx] == 1:
            signals.append("sklearn_isolation_forest")
        if xgb_residuals[idx] > np.percentile(xgb_residuals, 75):
            signals.append("xgboost_residual")
        if query_similarities[idx] > 0.35:
            signals.append("pytorch_query_similarity")

        if signals:
            unusual.append(
                {
                    "incident_id": inc.get("incident_id"),
                    "severity": inc.get("severity"),
                    "category": inc.get("category"),
                    "service": inc.get("service"),
                    "error_code": inc.get("error_code"),
                    "timestamp": inc.get("timestamp"),
                    "signals": signals,
                    "anomaly_score": float(anomaly_scores[idx]),
                    "xgb_residual": float(xgb_residuals[idx]),
                    "query_similarity": float(query_similarities[idx]) if idx < len(query_similarities) else 0.0,
                }
            )

    metrics = {
        "total_incidents": len(normalized),
        "total_candidates": len(normalized),
        "unusual_count": len(unusual),
        "unusual_rate": round(len(unusual) / max(len(normalized), 1), 3),
        "unique_categories": len(category_counts),
        "unique_services": len(service_counts),
        "unique_error_codes": len(error_counts),
    }

    top_patterns = [
        {
            "pattern": "top_categories",
            "values": category_counts.most_common(3),
        },
        {
            "pattern": "top_services",
            "values": service_counts.most_common(3),
        },
        {
            "pattern": "top_error_codes",
            "values": error_counts.most_common(3),
        },
    ]

    success_metrics = {
        "avg_anomaly_score": float(np.mean(anomaly_scores)) if len(anomaly_scores) else 0.0,
        "avg_xgb_residual": float(np.mean(xgb_residuals)) if len(xgb_residuals) else 0.0,
        "avg_query_similarity": float(np.mean(query_similarities)) if len(query_similarities) else 0.0,
    }

    return {
        "unusual_incidents": unusual,
        "metrics": metrics,
        "top_patterns": top_patterns,
        "success_metrics": success_metrics,
    }


@router.post("/query")
async def query_endpoint(
    request: QueryRequest,
    req: Request
):
    """
    Query endpoint - General purpose query interface
    Similar to OpenAI/Anthropic chat completion
    """
    try:
        request_id = getattr(req.state, "request_id", "unknown")
        logger.info(
            "V1 query start | query='%s' top_k=%s filter_type=%s include_reasoning=%s",
            request.query,
            request.top_k,
            request.filter_type,
            request.include_reasoning,
            extra={"request_id": request_id, "use_color": True},
        )
        vector_store = req.app.state.vector_store
        reasoning_engine = req.app.state.reasoning_engine
        
        if not vector_store or not reasoning_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform reasoning if requested
        if request.include_reasoning:
            reason_start = time.perf_counter()
            reasoning_result = await reasoning_engine.reason(
                query=request.query,
                max_steps=5
            )
            reason_ms = (time.perf_counter() - reason_start) * 1000
            logger.info(
                "V1 reasoning complete | intent=%s confidence=%.2f steps=%s duration_ms=%.2f",
                reasoning_result.get("intent"),
                reasoning_result.get("confidence", 0.0),
                len(reasoning_result.get("steps") or []),
                reason_ms,
                extra={"request_id": request_id, "use_color": True},
            )
            
            # Get additional context from vector store
            search_start = time.perf_counter()
            search_results = await vector_store.search(
                query=request.query,
                top_k=request.top_k,
                filter_type=request.filter_type
            )
            search_ms = (time.perf_counter() - search_start) * 1000
            logger.info(
                "V1 search complete | results=%s duration_ms=%.2f",
                len(search_results),
                search_ms,
                extra={"request_id": request_id, "use_color": True},
            )
            logger.info(
                "V1 search preview | %s",
                _summarize_context(search_results, max_items=2, preview_chars=120),
                extra={"request_id": request_id, "use_color": True},
            )
            logger.debug(
                "V1 search preview (full) | %s",
                _summarize_context(search_results),
                extra={"request_id": request_id},
            )
            
            return {
                "response": reasoning_result['final_answer'],
                "reasoning": {
                    "intent": reasoning_result['intent'],
                    "steps": reasoning_result['steps'],
                    "confidence": reasoning_result['confidence']
                },
                "context": [
                    {
                        "document": r.get('document', ''),
                        "type": r.get('metadata', {}).get('type', 'unknown') if isinstance(r.get('metadata'), dict) else 'unknown',
                        "score": r.get('score', 0.0)
                    }
                    for r in search_results
                ],
                "model": "vallm-v1",
                "usage": {
                    "tokens": len(request.query.split()),
                    "reasoning_steps": len(reasoning_result['steps'])
                }
            }
        else:
            # Simple search without reasoning
            search_start = time.perf_counter()
            search_results = await vector_store.search(
                query=request.query,
                top_k=request.top_k,
                filter_type=request.filter_type
            )
            search_ms = (time.perf_counter() - search_start) * 1000
            logger.info(
                "V1 search complete (no reasoning) | results=%s duration_ms=%.2f",
                len(search_results),
                search_ms,
                extra={"request_id": request_id, "use_color": True},
            )
            logger.info(
                "V1 search preview | %s",
                _summarize_context(search_results, max_items=2, preview_chars=120),
                extra={"request_id": request_id, "use_color": True},
            )
            logger.debug(
                "V1 search preview (full) | %s",
                _summarize_context(search_results),
                extra={"request_id": request_id},
            )

            # Simple response from top result
            if search_results:
                top_result = search_results[0]
                return {
                    "response": top_result.get('document', 'No content available'),
                    "context": [
                        {
                            "document": r.get('document', ''),
                            "type": r.get('metadata', {}).get('type', 'unknown') if isinstance(r.get('metadata'), dict) else 'unknown',
                            "score": r.get('score', 0.0)
                        }
                        for r in search_results
                    ],
                    "model": "vallm-v1",
                    "usage": {
                        "tokens": len(request.query.split())
                    }
                }
            else:
                return {
                    "response": "No relevant information found in the knowledge base.",
                    "context": [],
                    "model": "vallm-v1",
                    "usage": {
                        "tokens": len(request.query.split())
                    }
                }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        request_id = getattr(req.state, "request_id", "unknown")
        tb_str = traceback.format_exc()
        logger.error(f"V1 query failed [request_id={request_id}]\n{tb_str}")
        detail = f"Error processing query: {type(e).__name__}: {e or repr(e)}"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/developer")
async def developer_endpoint(
    request: DeveloperRequest,
    req: Request
):
    """
    Developer endpoint - For code generation and developer assistance
    Focuses on infrastructure as code, configurations, and automation
    """
    try:
        vector_store = req.app.state.vector_store
        reasoning_engine = req.app.state.reasoning_engine
        
        if not vector_store or not reasoning_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform reasoning with developer context
        reasoning_result = await reasoning_engine.reason(
            query=request.query,
            context=json.dumps(request.context) if request.context else None,
            max_steps=6
        )
        
        # Search for relevant configurations and code examples
        config_results = await vector_store.search(
            query=request.query,
            top_k=10,
            filter_type='configuration'
        )
        
        resource_results = await vector_store.search(
            query=request.query,
            top_k=5,
            filter_type='resource'
        )
        
        # Build developer-focused response
        response_parts = [reasoning_result['final_answer']]
        terraform_example = _build_terraform_example(request.query) if request.include_code else ""
        
        if request.include_code:
            response_parts.append("\n\n**Terraform (full example):**")
            response_parts.append(f"\n```terraform\n{terraform_example}\n```")

        if request.include_code and config_results:
            response_parts.append("\n\n**Relevant Configurations:**")
            for i, result in enumerate(config_results[:3], 1):
                response_parts.append(f"\n{i}. {result['document']}")
        
        if resource_results:
            response_parts.append("\n\n**Related Resources:**")
            for i, result in enumerate(resource_results[:3], 1):
                response_parts.append(f"\n{i}. {result['document']}")
        
        return {
            "response": "\n".join(response_parts),
            "reasoning": {
                "intent": reasoning_result['intent'],
                "steps": reasoning_result['steps'] if request.include_reasoning else None,
                "confidence": reasoning_result['confidence']
            },
            "code_examples": (
                [{
                    "type": "terraform",
                    "config": terraform_example,
                    "score": 1.0,
                }]
                + [
                    {
                        "type": r['metadata'].get('type'),
                        "config": r['document'],
                        "score": r['score']
                    }
                    for r in config_results[:5]
                ]
            ) if request.include_code else None,
            "model": "vallm-developer-v1",
            "usage": {
                "tokens": len(request.query.split()),
                "reasoning_steps": len(reasoning_result['steps'])
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing developer query: {str(e)}")


@router.post("/terminal")
async def terminal_endpoint(
    request: TerminalRequest,
    req: Request
):
    """
    Terminal endpoint - For command-line operations and terminal assistance
    Focuses on operational commands, troubleshooting, and system management
    """
    try:
        vector_store = req.app.state.vector_store
        reasoning_engine = req.app.state.reasoning_engine
        
        if not vector_store or not reasoning_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Search for relevant incidents and troubleshooting info
        incident_results = await vector_store.search(
            query=request.command,
            top_k=10,
            filter_type='incident'
        )
        
        recommendation_results = await vector_store.search(
            query=request.command,
            top_k=5,
            filter_type='recommendation'
        )
        
        # Perform reasoning
        reasoning_result = await reasoning_engine.reason(
            query=request.command,
            context=json.dumps(request.context) if request.context else None,
            max_steps=5
        )
        
        # Build terminal-focused response
        response_parts = []
        
        if request.include_explanation:
            response_parts.append(f"**Command Analysis:**\n{reasoning_result['final_answer']}")
        
        if incident_results:
            response_parts.append("\n\n**Similar Incidents:**")
            for i, result in enumerate(incident_results[:3], 1):
                incident_data = result['metadata'].get('raw_data', {})
                title = incident_data.get('title', 'Unknown')
                resolution = incident_data.get('resolution_time_minutes', 'N/A')
                response_parts.append(f"\n{i}. {title} (Resolution: {resolution} min)")
        
        if recommendation_results:
            response_parts.append("\n\n**Recommendations:**")
            for i, result in enumerate(recommendation_results[:3], 1):
                rec_data = result['metadata'].get('raw_data', {})
                rec_type = rec_data.get('recommendation_type', 'general')
                priority = rec_data.get('priority', 'medium')
                response_parts.append(f"\n{i}. [{priority.upper()}] {rec_type}: {result['document'][:200]}...")
        
        return {
            "response": "\n".join(response_parts),
            "command": request.command,
            "reasoning": {
                "intent": reasoning_result['intent'],
                "steps": reasoning_result['steps'] if request.include_explanation else None,
                "confidence": reasoning_result['confidence']
            },
            "incidents": [
                {
                    "title": r['metadata'].get('raw_data', {}).get('title', 'Unknown'),
                    "severity": r['metadata'].get('raw_data', {}).get('severity', 'unknown'),
                    "score": r['score']
                }
                for r in incident_results[:5]
            ],
            "recommendations": [
                {
                    "type": r['metadata'].get('raw_data', {}).get('recommendation_type', 'general'),
                    "priority": r['metadata'].get('raw_data', {}).get('priority', 'medium'),
                    "score": r['score']
                }
                for r in recommendation_results[:5]
            ],
            "model": "vallm-terminal-v1",
            "usage": {
                "tokens": len(request.command.split()),
                "reasoning_steps": len(reasoning_result['steps'])
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing terminal command: {str(e)}")


@router_v3.post("/query")
async def v3_query_endpoint(
    request: V3QueryRequest,
    req: Request
):
    """
    V3 Query endpoint - Cloud/DevOps incident pattern analysis with success metrics + Web Search.
    
    Now includes web search to find similar incidents, troubleshooting guides, and solutions
    from trusted sources like Stack Overflow, GitHub, HashiCorp, IBM, and vendor documentation.
    """
    try:
        request_id = getattr(req.state, "request_id", "unknown")
        logger.info(
            "V3 incident analysis start | query='%s' focus='%s' web_search=%s",
            request.query,
            request.focus,
            request.enable_web_search,
            extra={"request_id": request_id, "use_color": True},
        )
        
        vector_store = req.app.state.vector_store
        reasoning_engine = req.app.state.reasoning_engine

        if not vector_store or not reasoning_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")

        # Step 1: Local incident search
        local_start = time.perf_counter()
        search_results = await vector_store.search(
            query=request.query,
            top_k=request.top_k,
            filter_type="incident"
        )

        if request.focus == "cloud_devops":
            filtered = [
                r for r in search_results
                if _is_cloud_devops_incident(_normalize_incident_meta(r.get("metadata", {})))
            ]
        else:
            filtered = search_results
        
        local_ms = (time.perf_counter() - local_start) * 1000
        logger.info(
            "V3 local search complete | incidents=%s duration_ms=%.2f",
            len(filtered),
            local_ms,
            extra={"request_id": request_id, "use_color": True},
        )

        # Step 2: Analyze incident patterns
        analysis_start = time.perf_counter()
        analysis = analyze_unusual_incident_patterns_v3(vector_store, request.query, filtered)
        analysis_ms = (time.perf_counter() - analysis_start) * 1000

        # Step 3: Web search for similar incidents and solutions
        web_results_list = []
        trusted_count = 0
        web_ms = 0
        
        if request.enable_web_search:
            web_start = time.perf_counter()
            web_search = CloudDevOpsWebSearch(
                max_results=5,
                prioritize_sources=True
            )
            
            # Enhance query for incident troubleshooting
            incident_query = f"{request.query} troubleshooting solution incident resolution"
            web_results_list = web_search.search(incident_query, request.domain_focus)
            trusted_count = sum(1 for r in web_results_list if r.get('is_trusted', False))
            web_ms = (time.perf_counter() - web_start) * 1000
            
            logger.info(
                "V3 web search complete | results=%s trusted=%s duration_ms=%.2f",
                len(web_results_list),
                trusted_count,
                web_ms,
                extra={"request_id": request_id, "use_color": True},
            )

        # Step 4: Enhanced reasoning with web context
        if request.include_reasoning:
            reasoning_start = time.perf_counter()
            
            context_summary = {
                "unusual_count": analysis["metrics"]["unusual_count"],
                "top_patterns": analysis["top_patterns"],
            }
            
            # Add web search context if available
            if web_results_list:
                web_context = "\n\n### Web Search - Similar Incidents & Solutions:\n"
                for i, r in enumerate(web_results_list[:3], 1):
                    trusted = " [TRUSTED]" if r.get('is_trusted', False) else ""
                    web_context += f"{i}. {r['title']}{trusted}: {r['snippet'][:150]}...\n"
                context_summary["web_search_context"] = web_context
            
            reasoning_result = await reasoning_engine.reason(
                query=request.query,
                context=json.dumps(context_summary),
                max_steps=5
            )
            reasoning_ms = (time.perf_counter() - reasoning_start) * 1000
            
            # Build enhanced response
            response_text = reasoning_result["final_answer"]
            
            # Add web search insights
            if web_results_list:
                response_text += "\n\n### 🌐 Similar Incidents Found Online:\n"
                for i, r in enumerate(web_results_list[:5], 1):
                    trusted_badge = " ✓ **TRUSTED**" if r.get('is_trusted', False) else ""
                    source_cat = r.get('source_category', 'general')
                    response_text += f"\n**{i}. {r['title']}**{trusted_badge}\n"
                    response_text += f"   *Source: {source_cat}*\n"
                    response_text += f"   {r['snippet'][:200]}...\n"
                    response_text += f"   🔗 [{r['url']}]({r['url']})\n"
            
            reasoning_payload = {
                "intent": reasoning_result["intent"],
                "steps": reasoning_result["steps"],
                "confidence": reasoning_result["confidence"],
            }
            
            logger.info(
                "V3 reasoning complete | intent=%s confidence=%.2f duration_ms=%.2f",
                reasoning_result.get("intent"),
                reasoning_result.get("confidence", 0.0),
                reasoning_ms,
                extra={"request_id": request_id, "use_color": True},
            )
        else:
            response_text = "Incident pattern analysis completed."
            reasoning_payload = None
            reasoning_ms = 0

        return {
            "response": response_text,
            "query": request.query,
            "focus": request.focus,
            "unusual_incidents": analysis["unusual_incidents"],
            "metrics": analysis["metrics"],
            "top_patterns": analysis["top_patterns"],
            "success_metrics": analysis["success_metrics"],
            "reasoning": reasoning_payload,
            "web_search_results": web_results_list if request.enable_web_search else None,
            "trusted_sources": {
                "count": trusted_count,
                "total_results": len(web_results_list),
                "percentage": round((trusted_count / len(web_results_list) * 100), 1) if web_results_list else 0
            } if request.enable_web_search else None,
            "model": "vallm-v3-enhanced",
            "signals_used": ["embeddings", "vector_store", "sklearn", "xgboost", "pytorch"] + (["web_search"] if request.enable_web_search else []),
            "performance": {
                "local_search_ms": round(local_ms, 2),
                "analysis_ms": round(analysis_ms, 2),
                "web_search_ms": round(web_ms, 2) if request.enable_web_search else 0,
                "reasoning_ms": round(reasoning_ms, 2) if request.include_reasoning else 0,
                "total_ms": round(local_ms + analysis_ms + web_ms + reasoning_ms, 2)
            }
        }

    except Exception as e:
        import traceback
        request_id = getattr(req.state, "request_id", "unknown")
        tb_str = traceback.format_exc()
        logger.error(f"V3 query failed [request_id={request_id}]\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Error processing v3 query: {str(e)}")


@router.post("/query/websearch")
async def websearch_endpoint(
    request: WebSearchRequest,
    req: Request
):
    """
    Web Search Query endpoint - Combines web search with local RAG
    
    **Prioritizes Trusted Sources:**
    - Documentation: python.org, docs.aws.amazon.com, kubernetes.io, terraform.io
    - Community: stackoverflow.com, serverfault.com, github.com
    - Blogs: medium.com, dev.to, hashnode.com
    - Vendors: hashicorp.com, ibm.com, redhat.com
    - Monitoring: prometheus.io, grafana.com, datadoghq.com
    
    Domain focus options:
    - cloud: AWS, Azure, GCP, cloud infrastructure
    - devops: Kubernetes, Docker, CI/CD, automation
    - networking: VPC, DNS, load balancers, routing
    - observability: Monitoring, logging, metrics, tracing
    - programming: Coding, APIs, SDKs, languages
    - it_support: Troubleshooting, incident resolution
    """
    try:
        request_id = getattr(req.state, "request_id", "unknown")
        logger.info(
            "WebSearch query start | query='%s' domain='%s' deep=%s rag=%s",
            request.query,
            request.domain_focus,
            request.use_deep_search,
            request.combine_with_rag,
            extra={"request_id": request_id, "use_color": True},
        )
        
        vector_store = req.app.state.vector_store
        reasoning_engine = req.app.state.reasoning_engine
        
        if not vector_store or not reasoning_engine:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Initialize web search with trusted source prioritization
        web_search = CloudDevOpsWebSearch(
            max_results=request.top_k,
            prioritize_sources=True
        )
        
        # Perform web search
        search_start = time.perf_counter()
        if request.use_deep_search:
            web_results = web_search.deep_search(request.query, request.domain_focus)
            web_context = web_results.get("context", "")
            web_result_list = web_results.get("results", [])
            trusted_count = web_results.get("trusted_results", 0)
        else:
            web_result_list = web_search.search(request.query, request.domain_focus)
            trusted_count = sum(1 for r in web_result_list if r.get('is_trusted', False))
            web_context = "\n\n".join([
                f"**{r['title']}** {'✓ [TRUSTED]' if r.get('is_trusted') else ''}\n{r['snippet']}"
                for r in web_result_list
            ])
        search_ms = (time.perf_counter() - search_start) * 1000
        
        logger.info(
            "Web search complete | results=%s trusted=%s duration_ms=%.2f",
            len(web_result_list),
            trusted_count,
            search_ms,
            extra={"request_id": request_id, "use_color": True},
        )
        
        # Optionally combine with local RAG
        local_context = []
        rag_ms = 0
        if request.combine_with_rag:
            rag_start = time.perf_counter()
            local_results = await vector_store.search(
                query=request.query,
                top_k=request.top_k,
                filter_type=None
            )
            rag_ms = (time.perf_counter() - rag_start) * 1000
            
            local_context = [
                {
                    "document": r.get('document', ''),
                    "type": r.get('metadata', {}).get('type', 'unknown') if isinstance(r.get('metadata'), dict) else 'unknown',
                    "score": r.get('score', 0.0)
                }
                for r in local_results
            ]
            
            logger.info(
                "Local RAG complete | results=%s duration_ms=%.2f",
                len(local_results),
                rag_ms,
                extra={"request_id": request_id, "use_color": True},
            )
        
        # Perform reasoning with both web and local context
        reasoning_start = time.perf_counter()
        combined_context = f"### Web Search Results (Trusted Sources Prioritized):\n{web_context}\n\n### Local Knowledge:\n"
        if local_context:
            combined_context += "\n".join([f"- {c['document'][:200]}" for c in local_context[:3]])
        
        reasoning_result = await reasoning_engine.reason(
            query=request.query,
            context=combined_context,
            max_steps=5
        )
        reasoning_ms = (time.perf_counter() - reasoning_start) * 1000
        
        logger.info(
            "Reasoning complete | intent=%s confidence=%.2f duration_ms=%.2f",
            reasoning_result.get("intent"),
            reasoning_result.get("confidence", 0.0),
            reasoning_ms,
            extra={"request_id": request_id, "use_color": True},
        )
        
        # Build enhanced response with trusted source highlighting
        response_text = f"{reasoning_result['final_answer']}\n\n"
        response_text += f"### Web Search Results ({trusted_count} from trusted sources):\n"
        for i, r in enumerate(web_result_list[:5], 1):
            trusted_badge = " ✓ **TRUSTED**" if r.get('is_trusted', False) else ""
            source_cat = r.get('source_category', 'general')
            response_text += f"\n**{i}. {r['title']}**{trusted_badge}\n"
            response_text += f"   *Category: {source_cat}*\n"
            response_text += f"   {r['snippet'][:250]}...\n"
            response_text += f"   🔗 [Source]({r['url']})\n"
        
        return {
            "response": response_text,
            "query": request.query,
            "domain_focus": request.domain_focus,
            "web_results": web_result_list,
            "local_context": local_context if request.combine_with_rag else None,
            "reasoning": {
                "intent": reasoning_result['intent'],
                "steps": reasoning_result['steps'],
                "confidence": reasoning_result['confidence']
            },
            "trusted_sources": {
                "count": trusted_count,
                "total_results": len(web_result_list),
                "percentage": round((trusted_count / len(web_result_list) * 100), 1) if web_result_list else 0,
                "available_sources": web_search.get_all_trusted_sources()
            },
            "model": "vallm-websearch-v1",
            "usage": {
                "tokens": len(request.query.split()),
                "reasoning_steps": len(reasoning_result['steps']),
                "web_results_count": len(web_result_list),
                "local_results_count": len(local_context) if request.combine_with_rag else 0
            },
            "performance": {
                "web_search_ms": round(search_ms, 2),
                "rag_search_ms": round(rag_ms, 2),
                "reasoning_ms": round(reasoning_ms, 2),
                "total_ms": round(search_ms + rag_ms + reasoning_ms, 2)
            }
        }
    
    except Exception as e:
        import traceback
        request_id = getattr(req.state, "request_id", "unknown")
        tb_str = traceback.format_exc()
        logger.error(f"WebSearch query failed [request_id={request_id}]\n{tb_str}")
        detail = f"Error processing websearch query: {type(e).__name__}: {e or repr(e)}"
        raise HTTPException(status_code=500, detail=detail)

