"""
Model Management Service
Handles soft_delete, rename_alias, export_training_data
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
import logging

from .models import Model, ModelMetadata, ModelState, RequestLog, Eval, Tenant

logger = logging.getLogger("vallm")


class ModelService:
    """Service layer for model management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_model(self, model_id: str, tenant_id: str, include_deleted: bool = False) -> Optional[Model]:
        """Get model by ID for a tenant"""
        query = self.db.query(Model).filter(
            Model.id == model_id,
            Model.tenant_id == tenant_id
        )
        
        if not include_deleted:
            query = query.filter(Model.is_deleted == False)
        
        return query.first()
    
    def get_model_by_alias(self, alias: str, tenant_id: str) -> Optional[Model]:
        """Get model by alias"""
        return self.db.query(Model).filter(
            Model.alias == alias,
            Model.tenant_id == tenant_id,
            Model.is_deleted == False
        ).first()
    
    def list_models(
        self,
        tenant_id: str,
        state: Optional[ModelState] = None,
        include_deleted: bool = False
    ) -> List[Model]:
        """List models for a tenant"""
        query = self.db.query(Model).filter(Model.tenant_id == tenant_id)
        
        if state:
            query = query.filter(Model.state == state)
        
        if not include_deleted:
            query = query.filter(Model.is_deleted == False)
        
        return query.order_by(Model.created_at.desc()).all()
    
    def soft_delete_model(self, model_id: str, tenant_id: str) -> bool:
        """
        Soft delete a model
        Sets is_deleted=True and deleted_at timestamp
        """
        model = self.get_model(model_id, tenant_id, include_deleted=False)
        if not model:
            return False
        
        model.is_deleted = True
        model.deleted_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Model {model_id} soft deleted for tenant {tenant_id}")
        return True
    
    def restore_model(self, model_id: str, tenant_id: str) -> bool:
        """Restore a soft-deleted model"""
        model = self.get_model(model_id, tenant_id, include_deleted=True)
        if not model or not model.is_deleted:
            return False
        
        model.is_deleted = False
        model.deleted_at = None
        self.db.commit()
        
        logger.info(f"Model {model_id} restored for tenant {tenant_id}")
        return True
    
    def rename_alias(self, model_id: str, tenant_id: str, new_alias: str) -> bool:
        """
        Rename model alias
        Validates uniqueness within tenant scope
        """
        model = self.get_model(model_id, tenant_id)
        if not model:
            return False
        
        # Check if alias already exists for this tenant
        existing = self.get_model_by_alias(new_alias, tenant_id)
        if existing and existing.id != model_id:
            raise ValueError(f"Alias '{new_alias}' already exists for tenant {tenant_id}")
        
        old_alias = model.alias
        model.alias = new_alias
        model.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Model {model_id} alias renamed from '{old_alias}' to '{new_alias}'")
        return True
    
    def set_model_state(self, model_id: str, tenant_id: str, state: ModelState) -> bool:
        """Set model state (DRAFT, PRODUCTION, ARCHIVED)"""
        model = self.get_model(model_id, tenant_id)
        if not model:
            return False
        
        model.state = state
        model.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Model {model_id} state changed to {state.value}")
        return True
    
    def export_training_data(
        self,
        tenant_id: str,
        model_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_feedback_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Export tenant-specific training data as JSONL format
        Combines request logs and evaluation feedback
        """
        # Base query for request logs
        query = self.db.query(RequestLog).filter(
            RequestLog.tenant_id == tenant_id
        )
        
        if model_id:
            query = query.filter(RequestLog.model_id == model_id)
        
        if start_date:
            query = query.filter(RequestLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(RequestLog.created_at <= end_date)
        
        request_logs = query.order_by(RequestLog.created_at).all()
        
        # Get evaluations for context
        eval_query = self.db.query(Eval).filter(Eval.tenant_id == tenant_id)
        if model_id:
            eval_query = eval_query.filter(Eval.model_id == model_id)
        
        evals = {eval.request_id: eval for eval in eval_query.all()}
        
        # Build JSONL records
        training_data = []
        for log in request_logs:
            # Skip if only feedback is requested and no feedback exists
            if include_feedback_only and log.request_id not in evals:
                continue
            
            eval_data = evals.get(log.request_id)
            
            record = {
                "request_id": log.request_id,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "query": log.query,
                "prompt": log.prompt,
                "response": log.response,
                "metadata": log.log_metadata or {},
                "tokens": {
                    "input": log.tokens_input,
                    "output": log.tokens_output,
                    "total": log.tokens_used
                },
                "performance": {
                    "latency_ms": log.latency_ms
                }
            }
            
            # Add feedback if available
            if eval_data:
                record["feedback"] = {
                    "type": eval_data.feedback_type.value,
                    "value": eval_data.feedback_value,
                    "text": eval_data.feedback_text,
                    "reasoning_steps": eval_data.reasoning_steps
                }
            
            training_data.append(record)
        
        logger.info(
            f"Exported {len(training_data)} training records for tenant {tenant_id}"
            f"{f' (model {model_id})' if model_id else ''}"
        )
        
        return training_data
    
    def create_model(
        self,
        tenant_id: str,
        alias: str,
        model_path: str,
        version: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        ui_config_version: str = "1.0.0",
        ui_config: Optional[Dict[str, Any]] = None
    ) -> Model:
        """Create a new model with metadata"""
        # Check alias uniqueness
        existing = self.get_model_by_alias(alias, tenant_id)
        if existing:
            raise ValueError(f"Alias '{alias}' already exists for tenant {tenant_id}")
        
        model_id = str(uuid.uuid4())
        
        model = Model(
            id=model_id,
            tenant_id=tenant_id,
            alias=alias,
            model_path=model_path,
            version=version,
            description=description,
            created_by=created_by,
            state=ModelState.DRAFT
        )
        
        self.db.add(model)
        self.db.flush()  # Get model.id
        
        # Create metadata
        metadata = ModelMetadata(
            id=str(uuid.uuid4()),
            model_id=model_id,
            ui_config_version=ui_config_version,
            ui_config=ui_config or {}
        )
        
        self.db.add(metadata)
        self.db.commit()
        
        logger.info(f"Created model {model_id} ({alias}) for tenant {tenant_id}")
        return model
    
    def get_model_metadata(self, model_id: str, tenant_id: str) -> Optional[ModelMetadata]:
        """Get model metadata including UI config"""
        model = self.get_model(model_id, tenant_id)
        if not model:
            return None
        
        return self.db.query(ModelMetadata).filter(
            ModelMetadata.model_id == model_id
        ).first()
