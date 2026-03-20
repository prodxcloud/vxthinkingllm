"""
VaLLM Authentication via X-API-Key
====================================
Validates incoming requests against the tenants table.

Usage in routes:
    from app.auth.auth import require_api_key, get_caller_identity

    @router.post("/query")
    async def query(
        request: QueryRequest,
        caller: CallerIdentity = Depends(get_caller_identity),
    ):
        ...
"""

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader

logger = logging.getLogger("vallm")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Optional: hardcoded internal service key for service-to-service calls.
INTERNAL_SERVICE_KEY = os.getenv("VALLM_INTERNAL_SERVICE_KEY")

# Set VALLM_AUTH_DISABLED=true in dev to skip all auth checks.
AUTH_DISABLED = os.getenv("VALLM_AUTH_DISABLED", "false").lower() == "true"


def _hash_api_key(raw_key: str) -> str:
    """Hash a raw API key with SHA-256 to compare against token_hash in DB."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------

async def require_api_key(
    request: Request,
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> Optional[str]:
    """
    Validate the X-API-Key header.

    Returns the raw API key string on success.
    Raises 401 if missing or invalid.

    Supports three modes:
    1. AUTH_DISABLED=true  -> skip validation entirely (dev only)
    2. INTERNAL_SERVICE_KEY -> bypass DB if key matches (service-to-service)
    3. DB lookup           -> hash key and check tenants table
    """
    # Dev bypass
    if AUTH_DISABLED:
        return api_key or "dev-bypass"

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Internal service key bypass
    if INTERNAL_SERVICE_KEY and api_key == INTERNAL_SERVICE_KEY:
        return api_key

    # Database validation
    try:
        from app.orm.session import SessionLocal
        from app.orm.models import Tenant

        token_hash = _hash_api_key(api_key)
        db = SessionLocal()
        try:
            tenant_record = (
                db.query(Tenant)
                .filter(
                    Tenant.token_hash == token_hash,
                    Tenant.is_active == True,
                )
                .first()
            )
            if not tenant_record:
                raise HTTPException(status_code=401, detail="Invalid API key")

            if tenant_record.is_expired:
                raise HTTPException(status_code=401, detail="API key has expired")

            # Check if "vallm" service is allowed
            if tenant_record.disallowed_services:
                disallowed = tenant_record.disallowed_services
                if isinstance(disallowed, list) and "vallm" in disallowed:
                    raise HTTPException(status_code=403, detail="API key does not have access to VaLLM")
                elif isinstance(disallowed, dict) and disallowed.get("vallm"):
                    raise HTTPException(status_code=403, detail="API key does not have access to VaLLM")

            return api_key
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"API key validation failed (DB error): {e}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")


async def get_caller_identity(
    request: Request,
    api_key: str = Depends(require_api_key),
):
    """
    Resolve the full caller identity from the validated tenant key.
    Returns a CallerIdentity schema with tenant details.
    """
    from app.schemas.auth import CallerIdentity

    # Dev bypass returns a placeholder identity
    if AUTH_DISABLED:
        return CallerIdentity(
            tenant_id="dev-bypass",
            tenant_name="dev-tenant",
            email="dev@localhost",
            api_key_environment="DEVELOPMENT",
        )

    # Internal service key returns a service identity
    if INTERNAL_SERVICE_KEY and api_key == INTERNAL_SERVICE_KEY:
        return CallerIdentity(
            tenant_id="internal-service",
            tenant_name="infinityai-service",
            email="service@infinityai.local",
            api_key_environment="PRODUCTION",
        )

    # Full DB lookup
    try:
        from app.orm.session import SessionLocal
        from app.orm.models import Tenant

        token_hash = _hash_api_key(api_key)
        db = SessionLocal()
        try:
            tenant_record = (
                db.query(Tenant)
                .filter(Tenant.token_hash == token_hash, Tenant.is_active == True)
                .first()
            )
            if not tenant_record:
                raise HTTPException(status_code=401, detail="Invalid API key")

            return CallerIdentity(
                tenant_id=str(tenant_record.tenant_id),
                tenant_name=tenant_record.tenant_name,
                email=tenant_record.email,
                api_key_environment=tenant_record.environment,
                scopes=tenant_record.scopes,
            )
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Caller identity resolution failed: {e}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
