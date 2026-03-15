"""
Authentication Schemas for VaLLM
=================================
API key validation and caller identity schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


# ---------------------------------------------------------------------------
# API Key Schemas
# ---------------------------------------------------------------------------

class ApiKeyInfo(BaseSchema):
    """Public-facing API key info returned after validation."""
    id: Optional[str] = Field(None, description="UUID primary key")
    name: Optional[str] = Field(None, max_length=100)
    environment: Optional[str] = Field("DEVELOPMENT", max_length=20)
    is_active: Optional[bool] = True
    is_read_only: Optional[bool] = False
    rate_limit: Optional[int] = 1000
    scopes: Optional[Dict[str, Any]] = None
    allowed_services: Optional[Dict[str, Any]] = None
    last_used_at: Optional[datetime] = None
    usage_count: Optional[int] = 0


# ---------------------------------------------------------------------------
# Caller Identity (resolved from Developer key)
# ---------------------------------------------------------------------------

class CallerIdentity(BaseSchema):
    """Identity of the authenticated caller, resolved from the developer key."""
    developer_id: Optional[str] = None
    developer_name: str
    email: Optional[str] = None
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    api_key_name: str
    api_key_environment: str
    scopes: Optional[Dict[str, Any]] = None
