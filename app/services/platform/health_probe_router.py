"""
Health Probe API Router
Endpoints to check model warm/cold status
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from .database import get_db
from .models import Model
from .lifecycle_hooks import health_probe

router = APIRouter(prefix="/platform/health", tags=["Health Probes"])


@router.get("/models/{model_id}/status")
async def get_model_status(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Get model warm/cold status"""
    if not health_probe:
        raise HTTPException(status_code=503, detail="Health probe not initialized")
    
    # Verify model exists
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    status = health_probe.get_model_status(model_id)
    if not status:
        # Run a quick check
        from .lifecycle_hooks import HealthCheckProbe
        from fastapi import Request
        
        # We need app_state - this is a simplified version
        # In production, you'd pass app_state through dependency
        return {"message": "Status not available. Run health probe first."}
    
    return status


@router.get("/models/status")
async def get_all_model_statuses():
    """Get all model statuses"""
    if not health_probe:
        raise HTTPException(status_code=503, detail="Health probe not initialized")
    
    return health_probe.get_all_statuses()


@router.post("/models/{model_id}/warm")
async def warm_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger model warm-up
    (In production, this would load the model into memory)
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # TODO: Implement actual model loading
    return {
        "message": f"Model {model_id} warm-up requested",
        "note": "Model loading not implemented in this version"
    }
