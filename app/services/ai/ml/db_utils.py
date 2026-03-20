"""
Database Utilities for VaLLM ML Services
=========================================
Helper functions for saving queries, requests, and responses to the database.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request

# Ensure project root is on path so app.orm is importable (e.g. when run as app/app.py)
_root = Path(__file__).resolve().parents[4]  # va_llm_v1
if _root not in sys.path:
    sys.path.insert(0, str(_root))

# Handle both absolute and relative imports
SessionModel = None
get_db_context = None
try:
    from app.orm.models import Session as SessionModel
    from app.orm.session import get_db_context
except ImportError:
    try:
        from orm.models import Session as SessionModel
        from orm.session import get_db_context
    except ImportError:
        pass

logger = logging.getLogger("vallm")


def _default_tenant_id() -> Optional[str]:
    """Default tenant from .env (TENANT_ID); used when request does not provide tenant_id."""
    return os.getenv("TENANT_ID") or None


def get_client_info(request: Request) -> Dict[str, Optional[str]]:
    """Extract client IP and user agent from FastAPI Request."""
    client_ip = None
    user_agent = None
    
    if request.client:
        client_ip = request.client.host
    
    # Try to get real IP from headers (for proxied requests)
    if "x-forwarded-for" in request.headers:
        forwarded = request.headers["x-forwarded-for"]
        client_ip = forwarded.split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        client_ip = request.headers["x-real-ip"]
    
    user_agent = request.headers.get("user-agent")
    
    return {
        "client_ip": client_ip or "unknown",
        "user_agent": user_agent or "unknown"
    }


async def save_session_to_db(
    request: Request,
    query_text: Optional[str] = None,
    response_data: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    response_time_ms: float = 0.0,
    intent_detected: Optional[str] = None,
    confidence: Optional[float] = None,
    model_version: Optional[str] = None,
    tokens_used: Optional[int] = None,
    tenant_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Save a session record to the database.
    
    Args:
        request: FastAPI Request object
        query_text: The query text from the request
        response_data: The response data (will be stored in metadata)
        status_code: HTTP status code
        response_time_ms: Response time in milliseconds
        intent_detected: Detected intent from reasoning
        confidence: Confidence score
        model_version: Model version used
        tokens_used: Number of tokens used
        tenant_id: Optional tenant UUID
        metadata: Additional metadata to store
    
    Returns:
        Session ID (UUID string) if successful, None otherwise
    """
    if SessionModel is None or get_db_context is None:
        logger.debug("Database models not available - skipping session save")
        return None

    # Use request tenant_id or default from .env (TENANT_ID)
    effective_tenant_id = tenant_id or _default_tenant_id()
    
    try:
        client_info = get_client_info(request)
        
        # Prepare metadata
        session_metadata = metadata or {}
        if response_data:
            # Store response summary in metadata (avoid storing full response if too large)
            response_summary = {
                "has_response": True,
                "response_keys": list(response_data.keys()) if isinstance(response_data, dict) else [],
                "response_type": type(response_data).__name__
            }
            # Store full response if it's small enough (< 10KB when serialized)
            try:
                response_json = json.dumps(response_data)
                if len(response_json) < 10000:
                    response_summary["response"] = response_data
                else:
                    response_summary["response_preview"] = str(response_data)[:500]
            except:
                response_summary["response_preview"] = str(response_data)[:500]
            
            session_metadata["response"] = response_summary
        
        # Extract API version from path
        api_version = None
        path = str(request.url.path)
        if "/api/models/v1/" in path:
            api_version = "v1"
        elif "/api/models/v2/" in path:
            api_version = "v2"
        elif "/api/models/v3/" in path:
            api_version = "v3"
        elif "/api/cloud/" in path:
            api_version = "cloud"
        
        # Create session record
        with get_db_context() as db:
            session = SessionModel(
                tenant_id=effective_tenant_id,
                request_path=path,
                request_method=request.method,
                query_text=query_text,
                api_version=api_version,
                status_code=status_code,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used or 0,
                client_ip=client_info["client_ip"],
                user_agent=client_info["user_agent"][:500] if client_info["user_agent"] else None,
                intent_detected=intent_detected,
                confidence=confidence,
                model_version=model_version,
                metadata_=session_metadata
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            session_id = str(session.id)
            logger.debug(f"✅ Session saved to database: {session_id}")
            return session_id
            
    except Exception as e:
        # Don't fail the request if database save fails
        logger.error(f"❌ Failed to save session to database: {e}", exc_info=True)
        return None


def save_session_sync(
    request_path: str,
    request_method: str,
    query_text: Optional[str] = None,
    status_code: int = 200,
    response_time_ms: float = 0.0,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    intent_detected: Optional[str] = None,
    confidence: Optional[float] = None,
    model_version: Optional[str] = None,
    tokens_used: Optional[int] = None,
    tenant_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Synchronous version of save_session_to_db for use outside async context.
    
    Returns:
        Session ID (UUID string) if successful, None otherwise
    """
    if SessionModel is None or get_db_context is None:
        logger.debug("Database models not available - skipping session save")
        return None

    effective_tenant_id = tenant_id or _default_tenant_id()

    try:
        with get_db_context() as db:
            session = SessionModel(
                tenant_id=effective_tenant_id,
                request_path=request_path,
                request_method=request_method,
                query_text=query_text,
                api_version=None,
                status_code=status_code,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used or 0,
                client_ip=client_ip or "unknown",
                user_agent=(user_agent or "unknown")[:500],
                intent_detected=intent_detected,
                confidence=confidence,
                model_version=model_version,
                metadata_=metadata
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            session_id = str(session.id)
            logger.debug(f"✅ Session saved to database (sync): {session_id}")
            return session_id
            
    except Exception as e:
        logger.error(f"❌ Failed to save session to database (sync): {e}", exc_info=True)
        return None
