"""
Model Management API Router
Endpoints: soft_delete, rename_alias, export_training_data
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .database import get_db
from .model_service import ModelService
from .models import ModelState

router = APIRouter(prefix="/platform/models", tags=["Model Management"])


# Request/Response Models
class RenameAliasRequest(BaseModel):
    new_alias: str = Field(..., min_length=1, max_length=100)


class SetStateRequest(BaseModel):
    state: ModelState


class CreateModelRequest(BaseModel):
    alias: str = Field(..., min_length=1, max_length=100)
    model_path: str
    version: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    ui_config_version: str = "1.0.0"
    ui_config: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    id: str
    alias: str
    model_path: str
    state: str
    version: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    ui_config_version: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExportResponse(BaseModel):
    tenant_id: str
    model_id: Optional[str]
    record_count: int
    data: List[Dict[str, Any]]


def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")) -> str:
    """Extract tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
    return x_tenant_id


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    state: Optional[ModelState] = Query(None),
    include_deleted: bool = Query(False),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """List all models for a tenant"""
    service = ModelService(db)
    models = service.list_models(tenant_id, state, include_deleted)
    
    # Include metadata
    result = []
    for model in models:
        metadata = service.get_model_metadata(model.id, tenant_id)
        model_dict = {
            "id": model.id,
            "alias": model.alias,
            "model_path": model.model_path,
            "state": model.state.value,
            "version": model.version,
            "description": model.description,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "ui_config_version": metadata.ui_config_version if metadata else None
        }
        result.append(model_dict)
    
    return result


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Get model by ID"""
    service = ModelService(db)
    model = service.get_model(model_id, tenant_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    metadata = service.get_model_metadata(model_id, tenant_id)
    
    return {
        "id": model.id,
        "alias": model.alias,
        "model_path": model.model_path,
        "state": model.state.value,
        "version": model.version,
        "description": model.description,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "ui_config_version": metadata.ui_config_version if metadata else None
    }


@router.post("/", response_model=ModelResponse)
async def create_model(
    request: CreateModelRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Create a new model"""
    service = ModelService(db)
    
    try:
        model = service.create_model(
            tenant_id=tenant_id,
            alias=request.alias,
            model_path=request.model_path,
            version=request.version,
            description=request.description,
            created_by=request.created_by,
            ui_config_version=request.ui_config_version,
            ui_config=request.ui_config
        )
        
        metadata = service.get_model_metadata(model.id, tenant_id)
        
        return {
            "id": model.id,
            "alias": model.alias,
            "model_path": model.model_path,
            "state": model.state.value,
            "version": model.version,
            "description": model.description,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "ui_config_version": metadata.ui_config_version if metadata else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{model_id}")
async def soft_delete_model(
    model_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Soft delete a model"""
    service = ModelService(db)
    
    if not service.soft_delete_model(model_id, tenant_id):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"message": f"Model {model_id} soft deleted successfully"}


@router.post("/{model_id}/restore")
async def restore_model(
    model_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted model"""
    service = ModelService(db)
    
    if not service.restore_model(model_id, tenant_id):
        raise HTTPException(status_code=404, detail="Model not found or not deleted")
    
    return {"message": f"Model {model_id} restored successfully"}


@router.patch("/{model_id}/alias")
async def rename_alias(
    model_id: str,
    request: RenameAliasRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Rename model alias"""
    service = ModelService(db)
    
    try:
        if not service.rename_alias(model_id, tenant_id, request.new_alias):
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {"message": f"Alias updated to '{request.new_alias}'"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{model_id}/state")
async def set_model_state(
    model_id: str,
    request: SetStateRequest,
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Set model state (DRAFT, PRODUCTION, ARCHIVED)"""
    service = ModelService(db)
    
    if not service.set_model_state(model_id, tenant_id, request.state):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"message": f"Model state updated to {request.state.value}"}


@router.get("/{model_id}/export")
async def export_training_data(
    model_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_feedback_only: bool = Query(False),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Export training data for a model as JSONL
    Returns JSONL format suitable for fine-tuning
    """
    service = ModelService(db)
    
    # Verify model exists
    model = service.get_model(model_id, tenant_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    training_data = service.export_training_data(
        tenant_id=tenant_id,
        model_id=model_id,
        start_date=start_date,
        end_date=end_date,
        include_feedback_only=include_feedback_only
    )
    
    # Convert to JSONL string
    jsonl_lines = [json.dumps(record) for record in training_data]
    jsonl_content = "\n".join(jsonl_lines)
    
    from fastapi.responses import Response
    
    return Response(
        content=jsonl_content,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="training_data_{model_id}_{datetime.utcnow().strftime("%Y%m%d")}.jsonl"'
        }
    )


@router.get("/export/all")
async def export_all_training_data(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_feedback_only: bool = Query(False),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Export all training data for a tenant"""
    service = ModelService(db)
    
    training_data = service.export_training_data(
        tenant_id=tenant_id,
        model_id=None,
        start_date=start_date,
        end_date=end_date,
        include_feedback_only=include_feedback_only
    )
    
    jsonl_lines = [json.dumps(record) for record in training_data]
    jsonl_content = "\n".join(jsonl_lines)
    
    from fastapi.responses import Response
    
    return Response(
        content=jsonl_content,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="training_data_tenant_{tenant_id}_{datetime.utcnow().strftime("%Y%m%d")}.jsonl"'
        }
    )
