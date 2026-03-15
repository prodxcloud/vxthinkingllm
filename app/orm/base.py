"""
ORM Base Models & Mixins for VaLLM
====================================
Base classes for Developer and Tenant models.
"""

import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all VaLLM models."""
    pass


# ---------------------------------------------------------------------------
# Reusable Mixins
# ---------------------------------------------------------------------------

class TimestampMixin:
    """Adds created_at and updated_at columns."""
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class UUIDPrimaryKeyMixin:
    """UUID primary key."""
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
