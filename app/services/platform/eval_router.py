"""
Evaluation API Router
Endpoints for human-in-the-loop feedback
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from .database import get_db
from .eval_service import EvalService
from .models import FeedbackType

router = APIRouter(prefix="/platform/evals", tags=["Evaluation"])


class FeedbackRequest(BaseModel):
    request_id: str
    model_id: str
    feedback_type: FeedbackType
    feedback_value: int = Field(..., ge=-1, le=1)  # -1 for down, 1 for up
    feedback_text: Optional[str] = None
    query: Optional[str] = None
    response: Optional[str] = None
    prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    token_count: Optional[int] = None
    reasoning_steps: Optional[int] = None


class FeedbackResponse(BaseModel):
    id: str
    request_id: str
    model_id: str
    feedback_type: str
    feedback_value: int
    created_at: str
    
    class Config:
        from_attributes = True


def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")) -> str:
    """Extract tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
    return x_tenant_id


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Submit human-in-the-loop feedback (thumbs up/down)
    Links feedback to request_id for training data export
    """
    service = EvalService(db)
    
    try:
        eval_record = service.create_feedback(
            request_id=request.request_id,
            model_id=request.model_id,
            tenant_id=tenant_id,
            feedback_type=request.feedback_type,
            feedback_value=request.feedback_value,
            feedback_text=request.feedback_text,
            query=request.query,
            response=request.response,
            prompt=request.prompt,
            metadata=request.metadata,
            response_time_ms=request.response_time_ms,
            token_count=request.token_count,
            reasoning_steps=request.reasoning_steps
        )
        
        return {
            "id": eval_record.id,
            "request_id": eval_record.request_id,
            "model_id": eval_record.model_id,
            "feedback_type": eval_record.feedback_type.value,
            "feedback_value": eval_record.feedback_value,
            "created_at": eval_record.created_at.isoformat() if eval_record.created_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feedback/{request_id}")
async def get_feedback_by_request(
    request_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Get feedback for a specific request"""
    service = EvalService(db)
    eval_record = service.get_feedback_by_request(request_id, tenant_id)
    
    if not eval_record:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {
        "id": eval_record.id,
        "request_id": eval_record.request_id,
        "model_id": eval_record.model_id,
        "feedback_type": eval_record.feedback_type.value,
        "feedback_value": eval_record.feedback_value,
        "feedback_text": eval_record.feedback_text,
        "created_at": eval_record.created_at.isoformat() if eval_record.created_at else None
    }


@router.get("/stats")
async def get_feedback_stats(
    model_id: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Get feedback statistics for a tenant/model"""
    service = EvalService(db)
    return service.get_feedback_stats(tenant_id, model_id)


@router.get("/")
async def list_feedback(
    model_id: Optional[str] = None,
    feedback_type: Optional[FeedbackType] = None,
    limit: int = 100,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """List feedback records"""
    service = EvalService(db)
    evals = service.list_feedback(tenant_id, model_id, feedback_type, limit)
    
    return [
        {
            "id": e.id,
            "request_id": e.request_id,
            "model_id": e.model_id,
            "feedback_type": e.feedback_type.value,
            "feedback_value": e.feedback_value,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in evals
    ]
