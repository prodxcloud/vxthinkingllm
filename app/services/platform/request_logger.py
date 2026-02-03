"""
Request Logging Service
Logs requests for training data export
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from .models import RequestLog

logger = logging.getLogger("vallm")


class RequestLogger:
    """Service for logging API requests"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_request(
        self,
        request_id: str,
        tenant_id: str,
        endpoint: str,
        method: str,
        query: Optional[str] = None,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        tokens_used: int = 0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        latency_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        model_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RequestLog:
        """Log an API request"""
        
        log_entry = RequestLog(
            id=str(uuid.uuid4()),
            request_id=request_id,
            tenant_id=tenant_id,
            model_id=model_id,
            endpoint=endpoint,
            method=method,
            query=query,
            prompt=prompt,
            response=response,
            tokens_used=tokens_used,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            status_code=status_code,
            log_metadata=metadata or {}
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        return log_entry
