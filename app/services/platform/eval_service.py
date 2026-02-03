"""
Evaluation Service
Handles human-in-the-loop feedback (thumbs up/down)
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from .models import Eval, FeedbackType, Model, RequestLog

logger = logging.getLogger("vallm")


class EvalService:
    """Service layer for evaluation and feedback"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(
        self,
        request_id: str,
        model_id: str,
        tenant_id: str,
        feedback_type: FeedbackType,
        feedback_value: int,
        feedback_text: Optional[str] = None,
        query: Optional[str] = None,
        response: Optional[str] = None,
        prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        reasoning_steps: Optional[int] = None
    ) -> Eval:
        """Create evaluation feedback record"""
        
        # Verify model exists and belongs to tenant
        model = self.db.query(Model).filter(
            Model.id == model_id,
            Model.tenant_id == tenant_id,
            Model.is_deleted == False
        ).first()
        
        if not model:
            raise ValueError(f"Model {model_id} not found for tenant {tenant_id}")
        
        eval_record = Eval(
            id=str(uuid.uuid4()),
            request_id=request_id,
            model_id=model_id,
            tenant_id=tenant_id,
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            feedback_text=feedback_text,
            query=query,
            response=response,
            prompt=prompt,
            eval_metadata=metadata or {},
            response_time_ms=response_time_ms,
            token_count=token_count,
            reasoning_steps=reasoning_steps
        )
        
        self.db.add(eval_record)
        self.db.commit()
        
        logger.info(
            f"Feedback created: {feedback_type.value} for request {request_id} "
            f"(model {model_id}, tenant {tenant_id})"
        )
        
        return eval_record
    
    def get_feedback(self, eval_id: str, tenant_id: str) -> Optional[Eval]:
        """Get evaluation by ID"""
        return self.db.query(Eval).filter(
            Eval.id == eval_id,
            Eval.tenant_id == tenant_id
        ).first()
    
    def get_feedback_by_request(self, request_id: str, tenant_id: str) -> Optional[Eval]:
        """Get evaluation by request ID"""
        return self.db.query(Eval).filter(
            Eval.request_id == request_id,
            Eval.tenant_id == tenant_id
        ).first()
    
    def list_feedback(
        self,
        tenant_id: str,
        model_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 100
    ) -> list[Eval]:
        """List evaluations for a tenant"""
        query = self.db.query(Eval).filter(Eval.tenant_id == tenant_id)
        
        if model_id:
            query = query.filter(Eval.model_id == model_id)
        
        if feedback_type:
            query = query.filter(Eval.feedback_type == feedback_type)
        
        return query.order_by(Eval.created_at.desc()).limit(limit).all()
    
    def get_feedback_stats(
        self,
        tenant_id: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get feedback statistics"""
        query = self.db.query(Eval).filter(Eval.tenant_id == tenant_id)
        
        if model_id:
            query = query.filter(Eval.model_id == model_id)
        
        evals = query.all()
        
        total = len(evals)
        thumbs_up = sum(1 for e in evals if e.feedback_type == FeedbackType.THUMBS_UP and e.feedback_value > 0)
        thumbs_down = sum(1 for e in evals if e.feedback_type == FeedbackType.THUMBS_DOWN and e.feedback_value < 0)
        custom = sum(1 for e in evals if e.feedback_type == FeedbackType.CUSTOM)
        
        avg_response_time = sum(e.response_time_ms for e in evals if e.response_time_ms) / max(total, 1)
        avg_tokens = sum(e.token_count for e in evals if e.token_count) / max(total, 1)
        
        return {
            "total_feedback": total,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "custom": custom,
            "satisfaction_rate": round((thumbs_up / max(total, 1)) * 100, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_tokens": round(avg_tokens, 0)
        }
