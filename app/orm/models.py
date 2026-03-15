"""
ORM Models for VaLLM
=====================
Two tables only:
  - developers    : Developer API keys for authenticating requests
  - tenants       : Tenant registry (tracks where we deployed, with sub-users)
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.orm.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# 1. Tenant
# ---------------------------------------------------------------------------

class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tenant registry.
    Tracks where we deployed and who the sub-users are.
    A tenant can have many sub-users stored as JSON.
    """

    __tablename__ = "tenants"

    tenant_name = Column(String(255), nullable=False, unique=True)

    # Sub-users list stored as JSON array
    # e.g. [{"name": "Alice", "email": "alice@acme.com", "role": "admin"}, ...]
    tenants_sub_users = Column(JSONB, nullable=True, server_default="[]")

    # Relationships
    developers = relationship("Developer", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, tenant_name={self.tenant_name!r})>"


# ---------------------------------------------------------------------------
# 2. Developer (API Keys)
# ---------------------------------------------------------------------------

class Developer(Base, UUIDPrimaryKeyMixin):
    """
    Developer API key for authenticating requests to VaLLM.
    Each developer key is tied to a tenant.
    The token_hash is SHA-256 of the raw key issued.
    """

    __tablename__ = "developers"

    # Developer identity
    name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=True)
    description = Column(Text, nullable=True)

    # Tenant FK
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)

    # Key & environment
    environment = Column(String(20), nullable=False, default="DEVELOPMENT")
    token_hash = Column(String(128), nullable=False)

    # Scope & access
    allowed_services = Column(JSONB, nullable=True)
    disallowed_services = Column(JSONB, nullable=True)
    scopes = Column(JSONB, nullable=True)
    is_read_only = Column(Boolean, nullable=False, default=False)
    rate_limit = Column(Integer, nullable=False, default=1000)
    last_ip = Column(String(45), nullable=True)
    allowed_ips = Column(JSONB, nullable=True)

    # Timestamps & lifecycle
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)

    # Metadata
    metadata_ = Column("metadata", JSONB, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="developers")

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.is_active and not self.is_expired

    def __repr__(self) -> str:
        return f"<Developer(id={self.id}, name={self.name!r}, active={self.is_active})>"
