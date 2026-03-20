"""
Cloud provisioning intent API for VaLLM.

Returns structured intent + Golang-ready payload for provisioning requests only.
Non-provisioning queries return query_type "other". Used by InfinityAI cloud agent.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .entity_extraction import extract_entities_from_query

# Import database utilities
try:
    from app.services.ai.ml.db_utils import save_session_to_db
except ImportError:
    try:
        from .db_utils import save_session_to_db
    except ImportError:
        logger.warning("db_utils not available - database saving disabled")
        save_session_to_db = None

router = APIRouter(prefix="/api/cloud", tags=["cloud"])
logger = logging.getLogger("vallm.cloud")


class ProvisionIntentRequest(BaseModel):
    query: str


def _is_deployment_result(meta: Dict[str, Any]) -> bool:
    """True if this search result is from cloud_deployments (has intent in raw)."""
    raw = meta.get("raw") or {}
    return isinstance(raw, dict) and "intent" in raw and raw.get("intent")


def _raw_to_golang_payload(raw: Dict[str, Any], intent: str) -> Dict[str, Any]:
    """
    Map cloud_deployments CSV row (metadata.raw) to payload shape expected by
    Golang/InfinityAI provisionner_services (username, workspace, instance_type, etc.).
    """
    def v(key: str, default: str = "") -> str:
        val = raw.get(key)
        if val is None or (isinstance(val, str) and val.strip().lower() in ("", "nan")):
            return default
        return str(val).strip()

    def vi(key: str, default: int = 0) -> int:
        val = raw.get(key)
        if val is None or val == "":
            return default
        try:
            return int(float(str(val)))
        except (ValueError, TypeError):
            return default

    payload: Dict[str, Any] = {
        "username": v("username"),
        "tenant": v("tenant"),
        "tenant_id": v("tenant"),
        "user_id": v("username"),
    }

    if intent == "provision_vm":
        payload["instance_name"] = v("instance_name") or v("hostname")
        payload["resource_name"] = payload["instance_name"]
        payload["instance_type"] = v("instance_type", "t2.micro")
        payload["region"] = v("region", "us-east-1")
        payload["cloud_provider"] = v("cloud_provider", "aws")
        payload["os"] = v("os", "ubuntu")
        payload["volume_size"] = vi("volume_size_gb", 30)
        payload["volume_type"] = v("volume_type", "gp3")
        payload["environment"] = v("environment", "dev")
        payload["hostname"] = v("hostname")
        payload["ssh_username"] = v("ssh_username", "ubuntu")
        payload["key_pair_name"] = v("key_pair_name")

    elif intent == "provision_kubernetes":
        payload["cluster_name"] = v("cluster_name")
        payload["node_count"] = vi("node_count", 2)
        payload["node_type"] = v("node_type", "t3.medium")
        payload["kubernetes_version"] = v("kubernetes_version")
        payload["region"] = v("region", "us-east-1")
        payload["cloud_provider"] = v("cloud_provider", "aws")

    elif intent == "provision_docker":
        payload["docker_image"] = v("docker_image")
        payload["image"] = payload["docker_image"]
        payload["container_name"] = v("container_name") or v("docker_service")
        payload["docker_service"] = v("docker_service")
        payload["ports"] = v("ports")

    elif intent == "provision_fastapi":
        payload["hostname"] = v("hostname")
        payload["app_name"] = v("app_name")
        payload["app_port"] = vi("app_port", 8000)
        payload["http_port"] = vi("http_port", 8080)
        payload["ssh_username"] = v("ssh_username", "ubuntu")
        payload["key_pair_name"] = v("key_pair_name")

    elif intent == "provision_static_website":
        payload["hostname"] = v("hostname")
        payload["server_name"] = v("server_name")
        payload["http_port"] = vi("http_port", 80)
        payload["ssh_username"] = v("ssh_username", "ubuntu")
        payload["key_pair_name"] = v("key_pair_name")

    elif intent == "provision_database":
        payload["hostname"] = v("hostname")
        payload["database_engine"] = v("database_engine", "postgres")
        payload["database_name"] = v("database_name")
        payload["database_user"] = v("database_user")
        payload["postgres_version"] = v("postgres_version")
        payload["port"] = vi("port", 5432)
        payload["ssh_username"] = v("ssh_username", "ubuntu")
        payload["key_pair_name"] = v("key_pair_name")

    elif intent == "provision_github":
        payload["repo_name"] = v("repo_name")
        payload["visibility"] = v("visibility", "private")
        payload["default_branch"] = v("default_branch", "main")

    elif intent == "provision_github_actions":
        payload["repo_name"] = v("repo_name")
        payload["workflow_name"] = v("workflow_name")
        payload["runner_type"] = v("runner_type", "self-hosted")
        payload["cloud_provider"] = v("cloud_provider", "aws")
        payload["instance_type"] = v("instance_type", "t3.medium")
        payload["region"] = v("region", "us-east-1")
        payload["stack"] = v("stack")

    elif intent == "provision_cicd_pipeline":
        payload["pipeline_name"] = v("pipeline_name")
        payload["pipeline_type"] = v("pipeline_type")
        payload["repo_url"] = v("repo_url")
        payload["branch"] = v("branch", "main")
        payload["stages"] = v("stages", "build,test,deploy")

    elif intent == "provision_serverless":
        payload["function_name"] = v("function_name")
        payload["runtime"] = v("runtime", "python3.12")
        payload["handler"] = v("handler")
        payload["cloud_provider"] = v("cloud_provider", "aws")
        payload["region"] = v("region", "us-east-1")
        payload["trigger"] = v("trigger", "http")

    elif intent == "provision_cdn":
        payload["distribution_name"] = v("distribution_name")
        payload["origin"] = v("origin")
        payload["custom_domain"] = v("custom_domain")
        payload["cloud_provider"] = v("cloud_provider", "aws")

    elif intent == "provision_network":
        payload["vpc_name"] = v("vpc_name")
        payload["cidr_block"] = v("cidr_block", "10.0.0.0/16")
        payload["subnet_count"] = vi("subnet_count", 3)
        payload["region"] = v("region", "us-east-1")
        payload["cloud_provider"] = v("cloud_provider", "aws")

    elif intent == "provision_backup":
        payload["backup_target"] = v("backup_target")
        payload["schedule"] = v("schedule", "daily")
        payload["retention_days"] = vi("retention_days", 30)
        payload["storage_destination"] = v("storage_destination", "s3")

    elif intent == "provision_agent":
        payload["agent_name"] = v("agent_name")
        payload["model_name"] = v("model_name")
        payload["runtime"] = v("runtime", "docker")
        payload["gpu"] = v("gpu", "false")

    elif intent == "provision_workflow":
        payload["workflow_name"] = v("workflow_name")
        payload["steps"] = v("steps")
        payload["export_format"] = v("export_format", "terraform")

    # Common optional fields
    for key in ("region", "cloud_provider", "hostname", "ssh_username", "key_pair_name"):
        if key not in payload and v(key):
            payload[key] = v(key)

    return payload


def _classify_non_provisioning(query: str) -> str:
    """When no provisioning match, return 'other' only (provisioning-focused API)."""
    return "other"


def _ensure_complete_payload(payload: Dict[str, Any], intent: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure payload has all required fields based on intent and knowledge files.
    Follows cloud_operations_provisionning_knowledge1.txt and knowledge2.txt requirements.
    """
    def v(key: str, default: str = "") -> str:
        val = raw.get(key) or payload.get(key)
        if val is None or (isinstance(val, str) and val.strip().lower() in ("", "nan")):
            return default
        return str(val).strip()
    
    # Add common required fields
    if "username" not in payload or not payload["username"]:
        payload["username"] = v("username", "default_user")
    
    if "cloud_provider" not in payload or not payload["cloud_provider"]:
        payload["cloud_provider"] = v("cloud_provider", "aws")
    
    if "region" not in payload or not payload["region"]:
        payload["region"] = v("region", "us-east-1")
    
    # Intent-specific required fields based on knowledge files
    if intent == "provision_vm":
        if "instance_type" not in payload or not payload["instance_type"]:
            payload["instance_type"] = v("instance_type", "t2.micro")
        if "os" not in payload or not payload["os"]:
            payload["os"] = v("os", "ubuntu")
        if "volume_size" not in payload:
            payload["volume_size"] = int(v("volume_size_gb", "30"))
        if "volume_type" not in payload or not payload["volume_type"]:
            payload["volume_type"] = v("volume_type", "gp3")
        if "environment" not in payload or not payload["environment"]:
            payload["environment"] = v("environment", "dev")
        if "instance_name" not in payload or not payload["instance_name"]:
            payload["instance_name"] = v("instance_name") or v("hostname") or f"vm-{int(time.time())}"
        if "resource_name" not in payload:
            payload["resource_name"] = payload["instance_name"]
        if "ssh_username" not in payload or not payload["ssh_username"]:
            payload["ssh_username"] = v("ssh_username", "ubuntu")
    
    elif intent == "provision_kubernetes":
        if "cluster_name" not in payload or not payload["cluster_name"]:
            payload["cluster_name"] = v("cluster_name") or f"k8s-cluster-{int(time.time())}"
        if "node_count" not in payload:
            payload["node_count"] = int(v("node_count", "2"))
        if "node_type" not in payload or not payload["node_type"]:
            payload["node_type"] = v("node_type", "t3.medium")
        if "kubernetes_version" not in payload or not payload["kubernetes_version"]:
            payload["kubernetes_version"] = v("kubernetes_version", "1.28")
    
    elif intent == "provision_docker":
        if "docker_image" not in payload or not payload["docker_image"]:
            payload["docker_image"] = v("docker_image", "nginx:latest")
        if "container_name" not in payload or not payload["container_name"]:
            payload["container_name"] = v("container_name") or f"container-{int(time.time())}"
        if "ports" not in payload or not payload["ports"]:
            # Default ports based on image
            image = payload.get("docker_image", "").lower()
            if "nginx" in image:
                payload["ports"] = "80:80"
            elif "postgres" in image:
                payload["ports"] = "5432:5432"
            elif "redis" in image:
                payload["ports"] = "6379:6379"
            else:
                payload["ports"] = v("ports", "8080:8080")
        if "hostname" not in payload or not payload["hostname"]:
            payload["hostname"] = v("hostname", "")
        if "ssh_username" not in payload or not payload["ssh_username"]:
            payload["ssh_username"] = v("ssh_username", "ubuntu")
        if "key_pair_name" not in payload or not payload["key_pair_name"]:
            payload["key_pair_name"] = v("key_pair_name", "")
    
    elif intent == "provision_fastapi":
        if "hostname" not in payload or not payload["hostname"]:
            payload["hostname"] = v("hostname", "")
        if "app_name" not in payload or not payload["app_name"]:
            payload["app_name"] = v("app_name") or f"fastapi-app-{int(time.time())}"
        if "app_port" not in payload:
            payload["app_port"] = int(v("app_port", "8000"))
        if "http_port" not in payload:
            payload["http_port"] = int(v("http_port", "80"))
        if "ssh_username" not in payload or not payload["ssh_username"]:
            payload["ssh_username"] = v("ssh_username", "ubuntu")
        if "key_pair_name" not in payload or not payload["key_pair_name"]:
            payload["key_pair_name"] = v("key_pair_name", "")
    
    elif intent == "provision_static_website":
        if "hostname" not in payload or not payload["hostname"]:
            payload["hostname"] = v("hostname", "")
        if "server_name" not in payload or not payload["server_name"]:
            # server_name MUST always match hostname per knowledge file
            payload["server_name"] = payload.get("hostname", "") or v("server_name", "")
        if "http_port" not in payload:
            payload["http_port"] = int(v("http_port", "80"))
        if "ssh_username" not in payload or not payload["ssh_username"]:
            payload["ssh_username"] = v("ssh_username", "ubuntu")
        if "key_pair_name" not in payload or not payload["key_pair_name"]:
            payload["key_pair_name"] = v("key_pair_name", "")
    
    elif intent == "provision_database":
        if "hostname" not in payload or not payload["hostname"]:
            payload["hostname"] = v("hostname", "")
        if "database_engine" not in payload or not payload["database_engine"]:
            payload["database_engine"] = v("database_engine", "postgres")
        if "database_name" not in payload or not payload["database_name"]:
            payload["database_name"] = v("database_name") or f"db-{int(time.time())}"
        if "database_user" not in payload or not payload["database_user"]:
            payload["database_user"] = v("database_user", "admin")
        if "port" not in payload:
            # Default ports based on engine
            engine = payload.get("database_engine", "").lower()
            if "postgres" in engine:
                payload["port"] = int(v("port", "5432"))
            elif "mysql" in engine or "mariadb" in engine:
                payload["port"] = int(v("port", "3306"))
            elif "mongodb" in engine:
                payload["port"] = int(v("port", "27017"))
            else:
                payload["port"] = int(v("port", "5432"))
        if "ssh_username" not in payload or not payload["ssh_username"]:
            payload["ssh_username"] = v("ssh_username", "ubuntu")
        if "key_pair_name" not in payload or not payload["key_pair_name"]:
            payload["key_pair_name"] = v("key_pair_name", "")
    
    return payload


@router.post("/provision-intent")
async def provision_intent(
    request: ProvisionIntentRequest,
    req: Request,
):
    """
    Resolve user message to provisioning intent + Golang-ready payload.
    When no deployment match: returns query_type "other". Provisioning-only.
    """
    start_time = time.perf_counter()
    status_code = 200
    intent_detected = None
    confidence = None
    
    vector_store = getattr(req.app.state, "vector_store", None)
    if not vector_store:
        status_code = 503
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    query = (request.query or "").strip()
    if not query:
        response_data = {
            "query_type": "other",
            "intent": None,
            "payload": None,
            "confidence": 0.0,
            "match_prompt": None,
        }
        
        # Save to database
        if save_session_to_db:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            await save_session_to_db(
                request=req,
                query_text="",
                response_data=response_data,
                status_code=status_code,
                response_time_ms=response_time_ms,
                model_version="cloud-provision-intent",
                metadata={"query_type": "other", "empty_query": True}
            )
        
        return response_data

    # Search; prefer deployment-type results if precompute tags them (filter_type="deployment")
    try:
        search_results = await vector_store.search(
            query=query,
            top_k=20,
            filter_type=None,
        )
    except Exception as e:
        logger.exception("provision-intent search failed")
        status_code = 500
        # Save error to database
        if save_session_to_db:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            await save_session_to_db(
                request=req,
                query_text=query,
                response_data={"error": str(e)},
                status_code=status_code,
                response_time_ms=response_time_ms,
                model_version="cloud-provision-intent"
            )
        raise HTTPException(status_code=500, detail=str(e))

    # Keep only rows from cloud_deployments (raw has "intent")
    deployment_results: List[Dict[str, Any]] = [
        r for r in search_results
        if _is_deployment_result(r.get("metadata") or {})
    ]

    if not deployment_results:
        query_type = _classify_non_provisioning(query)
        response_data = {
            "query_type": query_type,
            "intent": None,
            "payload": None,
            "confidence": 0.0,
            "match_prompt": None,
        }
        
        # Save to database
        if save_session_to_db:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            await save_session_to_db(
                request=req,
                query_text=query,
                response_data=response_data,
                status_code=status_code,
                response_time_ms=response_time_ms,
                model_version="cloud-provision-intent",
                metadata={"query_type": query_type}
            )
        
        return response_data

    best = deployment_results[0]
    meta = best.get("metadata") or {}
    raw = meta.get("raw") or {}
    intent = raw.get("intent", "")
    score = best.get("score", 0.0)
    match_prompt = raw.get("prompt", "")

    # Require minimum confidence (e.g. score > 0.3 for cosine-like scores; adjust if your metric differs)
    confidence = float(score)
    if confidence < 0.3:
        query_type = _classify_non_provisioning(query)
        response_data = {
            "query_type": query_type,
            "intent": None,
            "payload": None,
            "confidence": confidence,
            "match_prompt": match_prompt,
        }
        
        # Save to database
        if save_session_to_db:
            response_time_ms = (time.perf_counter() - start_time) * 1000
            await save_session_to_db(
                request=req,
                query_text=query,
                response_data=response_data,
                status_code=status_code,
                response_time_ms=response_time_ms,
                confidence=confidence,
                model_version="cloud-provision-intent",
                metadata={"query_type": query_type}
            )
        
        return response_data

    # Build complete payload following knowledge files structure
    payload = _raw_to_golang_payload(raw, intent)
    
    # Extract entities from user query and override matched values
    extracted_entities = extract_entities_from_query(query)
    if extracted_entities:
        logger.info(f"Overriding matched payload with extracted entities: {extracted_entities}")
        payload.update(extracted_entities)
    
    # Ensure all required fields are present based on intent and knowledge files
    payload = _ensure_complete_payload(payload, intent, raw)
    
    response_data = {
        "query_type": "provisioning",
        "intent": intent,
        "payload": payload,
        "confidence": confidence,
        "match_prompt": match_prompt,
        "metadata": {
            "source": "knowledge_base",
            "matched_document": best.get("document", "")[:200] if best.get("document") else None,
            "search_score": score,
            "deployment_matches": len(deployment_results),
        }
    }
    
    intent_detected = intent
    
    # Save to database
    if save_session_to_db:
        response_time_ms = (time.perf_counter() - start_time) * 1000
        await save_session_to_db(
            request=req,
            query_text=query,
            response_data=response_data,
            status_code=status_code,
            response_time_ms=response_time_ms,
            intent_detected=intent_detected,
            confidence=confidence,
            model_version="cloud-provision-intent",
            metadata={"query_type": "provisioning", "intent": intent}
        )
    
    return response_data
