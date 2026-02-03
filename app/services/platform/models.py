"""
Database Models for Platform Infrastructure
Includes: Models, ModelMetadata, Evals, Tenants
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base


class ModelState(str, enum.Enum):
    """Model deployment state"""
    DRAFT = "draft"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class FeedbackType(str, enum.Enum):
    """Human feedback type"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    CUSTOM = "custom"


class Tenant(Base):
    """Tenant model for multi-tenancy"""
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True, index=True)  # tenant_id
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Rate limiting config per tenant
    tpm_limit = Column(Integer, default=1000000)  # Tokens per minute
    rpm_limit = Column(Integer, default=100)  # Requests per minute (fallback)
    
    # Relationships
    models = relationship("Model", back_populates="tenant")
    evals = relationship("Eval", back_populates="tenant")
    request_logs = relationship("RequestLog", back_populates="tenant")


class Model(Base):
    """Model registry with draft/production states"""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True, index=True)  # model_id (UUID)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    alias = Column(String, unique=True, index=True)  # Human-readable alias
    model_path = Column(String, nullable=False)  # Path to model weights
    state = Column(SQLEnum(ModelState), default=ModelState.DRAFT, index=True)
    
    # Model metadata
    version = Column(String, nullable=False)  # Semantic version
    description = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="models")
    ui_metadata = relationship("ModelMetadata", back_populates="model", uselist=False)
    evals = relationship("Eval", back_populates="model")


class ModelMetadata(Base):
    """Model metadata including UI configuration versioning"""
    __tablename__ = "model_metadata"
    
    id = Column(String, primary_key=True, index=True)
    model_id = Column(String, ForeignKey("models.id"), unique=True, nullable=False)
    
    # UI Configuration Versioning
    ui_config_version = Column(String, nullable=False, default="1.0.0")
    ui_config = Column(JSON, default=dict)  # Flexible JSON for UI components
    
    # Model capabilities
    supports_streaming = Column(Boolean, default=False)
    supports_function_calling = Column(Boolean, default=False)
    max_tokens = Column(Integer, default=2048)
    temperature_range = Column(JSON, default={"min": 0.0, "max": 2.0})
    
    # Prompt fields configuration (for frontend rendering)
    prompt_fields = Column(JSON, default=list)  # List of prompt field definitions
    # Example: [{"name": "system_prompt", "type": "textarea", "required": true, ...}]
    
    # Model performance metrics
    avg_latency_ms = Column(Float)
    avg_tokens_per_second = Column(Float)
    accuracy_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    model = relationship("Model", back_populates="ui_metadata")


class Eval(Base):
    """Evaluation records for human-in-the-loop feedback"""
    __tablename__ = "evals"
    
    id = Column(String, primary_key=True, index=True)  # eval_id (UUID)
    request_id = Column(String, nullable=False, index=True)  # Links to request
    model_id = Column(String, ForeignKey("models.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Feedback
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    feedback_value = Column(Integer)  # 1 for thumbs_up, -1 for thumbs_down, or custom
    feedback_text = Column(Text)  # Optional text feedback
    
    # Request context (for training data export)
    query = Column(Text)
    response = Column(Text)
    prompt = Column(Text)
    eval_metadata = Column(JSON, default=dict)  # Additional context
    
    # Evaluation metrics
    response_time_ms = Column(Float)
    token_count = Column(Integer)
    reasoning_steps = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    model = relationship("Model", back_populates="evals")
    tenant = relationship("Tenant", back_populates="evals")


class RequestLog(Base):
    """Request logs for training data export"""
    __tablename__ = "request_logs"
    
    id = Column(String, primary_key=True, index=True)  # log_id (UUID)
    request_id = Column(String, nullable=False, unique=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    model_id = Column(String, ForeignKey("models.id"), nullable=True, index=True)
    
    # Request details
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    query = Column(Text)
    prompt = Column(Text)
    response = Column(Text)
    
    # Token tracking for rate limiting
    tokens_used = Column(Integer, default=0)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    
    # Performance
    latency_ms = Column(Float)
    status_code = Column(Integer)
    
    # Metadata
    log_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship
    tenant = relationship("Tenant", back_populates="request_logs")
