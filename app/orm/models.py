"""
ORM Models for VaLLM
=====================
Two tables only:
  - tenants     : Tenant registry with API key auth and sub-tenant management
  - sessions    : Records every session and request against VaLLM
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    Float, func, ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.orm.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, TenantPrimaryKeyMixin


# ---------------------------------------------------------------------------
# 1. Tenant
# ---------------------------------------------------------------------------

class Tenant(Base, TenantPrimaryKeyMixin, TimestampMixin):
    """
    Tenant registry with built-in API key authentication.
    Tracks where VaLLM is deployed, who the sub-tenants are,
    and manages access control per tenant.
    """

    __tablename__ = "tenants"

    # --- Identity ---
    tenant_name = Column(String(255), nullable=False, unique=True)
    email = Column(String(254), nullable=True)
    description = Column(Text, nullable=True)

    # --- Sub-tenants ---
    # e.g. [{"name": "Alice", "email": "alice@acme.com", "role": "admin"}, ...]
    sub_tenants = Column(JSONB, nullable=True, server_default="[]")

    # --- API Key & Environment ---
    token_hash = Column(String(128), nullable=False)
    environment = Column(String(20), nullable=False, default="DEVELOPMENT")

    # --- Scope & Access Control ---
    allowed_services = Column(JSONB, nullable=True)
    disallowed_services = Column(JSONB, nullable=True)
    scopes = Column(JSONB, nullable=True)
    is_read_only = Column(Boolean, nullable=False, default=False)
    rate_limit = Column(Integer, nullable=False, default=1000)
    last_ip = Column(String(45), nullable=True)
    allowed_ips = Column(JSONB, nullable=True)

    # --- Lifecycle ---
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)

    # --- Metadata ---
    metadata_ = Column("metadata", JSONB, nullable=True)

    # --- Relationships ---
    sessions = relationship("Session", back_populates="tenant")

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.is_active and not self.is_expired

    def __repr__(self) -> str:
        return f"<Tenant(tenant_id={self.tenant_id}, tenant_name={self.tenant_name!r}, active={self.is_active})>"


# ---------------------------------------------------------------------------
# 2. Session (request log)
# ---------------------------------------------------------------------------

class Session(Base, UUIDPrimaryKeyMixin):
    """
    Records every session and request against VaLLM.
    Used for audit logging, usage analytics, and billing.
    """

    __tablename__ = "sessions"

    # --- Tenant FK ---
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=True, index=True)

    # --- Request details ---
    request_path = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    query_text = Column(Text, nullable=True)
    api_version = Column(String(10), nullable=True)

    # --- Response details ---
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True, default=0)

    # --- Client info ---
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # --- Result metadata ---
    intent_detected = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # --- Extra ---
    metadata_ = Column("metadata", JSONB, nullable=True)

    # --- Relationships ---
    tenant = relationship("Tenant", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, tenant_id={self.tenant_id}, path={self.request_path!r})>"
