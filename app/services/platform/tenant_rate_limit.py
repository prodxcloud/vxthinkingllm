"""
Tenant-Aware Rate Limiting Middleware
Uses Redis to limit based on Tokens Per Minute (TPM) per tenant
"""
import os
import json
from fastapi import Request, HTTPException, Header
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional
import time
import logging

logger = logging.getLogger("vallm")

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Install with: pip install redis")

# Configuration
RATE_LIMIT_ENABLED = os.getenv("VALLM_TENANT_RATE_LIMIT_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Default TPM limits (can be overridden per tenant in database)
DEFAULT_TPM_LIMIT = int(os.getenv("VALLM_DEFAULT_TPM_LIMIT", "1000000"))  # 1M tokens/min
DEFAULT_RPM_LIMIT = int(os.getenv("VALLM_DEFAULT_RPM_LIMIT", "100"))  # Fallback: requests/min


class TenantRateLimiter:
    """Redis-based tenant rate limiter using Token Per Minute (TPM)"""
    
    def __init__(self):
        if not REDIS_AVAILABLE:
            self.redis_client = None
            logger.warning("Redis not available - rate limiting disabled")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _get_tenant_limits(self, tenant_id: str) -> tuple[int, int]:
        """
        Get TPM and RPM limits for a tenant
        In production, this would query the database
        For now, returns defaults
        """
        # TODO: Query database for tenant-specific limits
        # For now, use defaults
        return DEFAULT_TPM_LIMIT, DEFAULT_RPM_LIMIT
    
    def _estimate_tokens(self, text: Optional[str]) -> int:
        """Estimate token count (simple approximation: ~4 chars per token)"""
        if not text:
            return 0
        return len(text) // 4
    
    def check_tpm_limit(
        self,
        tenant_id: str,
        tokens_used: int,
        window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """
        Check if tenant has exceeded TPM limit
        Returns: (allowed, remaining_tokens, reset_seconds)
        """
        if not self.redis_client:
            return True, DEFAULT_TPM_LIMIT, 0
        
        try:
            tpm_limit, _ = self._get_tenant_limits(tenant_id)
            key = f"rate_limit:tpm:{tenant_id}"
            
            # Get current usage
            current_usage = self.redis_client.get(key)
            if current_usage is None:
                current_usage = 0
            else:
                current_usage = int(current_usage)
            
            # Check if limit exceeded
            if current_usage + tokens_used > tpm_limit:
                # Get TTL to know when limit resets
                ttl = self.redis_client.ttl(key)
                reset_seconds = max(ttl, 0) if ttl > 0 else window_seconds
                return False, max(0, tpm_limit - current_usage), reset_seconds
            
            # Increment usage
            pipe = self.redis_client.pipeline()
            pipe.incrby(key, tokens_used)
            pipe.expire(key, window_seconds)
            pipe.execute()
            
            remaining = tpm_limit - (current_usage + tokens_used)
            return True, remaining, window_seconds
            
        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return True, DEFAULT_TPM_LIMIT, 0
    
    def check_rpm_limit(
        self,
        tenant_id: str,
        window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """
        Fallback: Check requests per minute limit
        Returns: (allowed, remaining_requests, reset_seconds)
        """
        if not self.redis_client:
            return True, DEFAULT_RPM_LIMIT, 0
        
        try:
            _, rpm_limit = self._get_tenant_limits(tenant_id)
            key = f"rate_limit:rpm:{tenant_id}"
            
            current_count = self.redis_client.get(key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            if current_count >= rpm_limit:
                ttl = self.redis_client.ttl(key)
                reset_seconds = max(ttl, 0) if ttl > 0 else window_seconds
                return False, 0, reset_seconds
            
            # Increment count
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            pipe.execute()
            
            remaining = rpm_limit - (current_count + 1)
            return True, remaining, window_seconds
            
        except Exception as e:
            logger.error(f"Redis error in RPM rate limiting: {e}")
            return True, DEFAULT_RPM_LIMIT, 0


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for tenant-aware rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = TenantRateLimiter() if RATE_LIMIT_ENABLED else None
    
    async def dispatch(self, request: Request, call_next):
        # Skip if rate limiting disabled
        if not RATE_LIMIT_ENABLED or not self.rate_limiter:
            return await call_next(request)
        
        # Get tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            # Allow requests without tenant ID (legacy support)
            # In production, you might want to reject these
            return await call_next(request)
        
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/health/ready", "/health/live", "/metrics"]:
            return await call_next(request)
        
        # Estimate tokens from request body (if available)
        tokens_estimate = 0
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse JSON and estimate tokens
                    try:
                        body_json = json.loads(body.decode())
                        # Estimate from query/prompt fields
                        query_text = ""
                        if isinstance(body_json, dict):
                            query_text = body_json.get("query", "") or body_json.get("prompt", "") or ""
                        tokens_estimate = self.rate_limiter._estimate_tokens(query_text)
                    except:
                        # Fallback: estimate from raw body
                        tokens_estimate = self.rate_limiter._estimate_tokens(body.decode(errors="ignore"))
                
                # Reset body for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except:
                pass
        
        # Check TPM limit
        allowed, remaining_tokens, reset_seconds = self.rate_limiter.check_tpm_limit(
            tenant_id, tokens_estimate
        )
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: Token limit reached",
                headers={
                    "X-RateLimit-Limit": str(DEFAULT_TPM_LIMIT),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_seconds),
                    "Retry-After": str(reset_seconds)
                }
            )
        
        # Also check RPM as fallback (for very small requests)
        if tokens_estimate < 10:  # Only check RPM for tiny requests
            allowed_rpm, remaining_rpm, reset_seconds_rpm = self.rate_limiter.check_rpm_limit(tenant_id)
            if not allowed_rpm:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded: Request limit reached",
                    headers={
                        "X-RateLimit-Limit": str(DEFAULT_RPM_LIMIT),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + reset_seconds_rpm),
                        "Retry-After": str(reset_seconds_rpm)
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Update rate limit headers
        response.headers["X-RateLimit-Limit"] = str(DEFAULT_TPM_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(remaining_tokens)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_seconds)
        
        return response
