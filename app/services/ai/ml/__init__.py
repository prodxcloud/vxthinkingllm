"""
VaLLM ML Services - Machine Learning and AI components
"""

__version__ = "1.0.0"

# Core ML components
from .embeddings import VectorStore, embedding_service
from .reasoning import ReasoningEngine
from .cache import TTLCache, get_embedding_cache, get_search_cache, get_all_cache_stats
from .metrics import (
    http_requests_total,
    http_request_duration_seconds,
    errors_total,
    get_metrics_response,
    normalize_path,
)
from .health import HealthChecker
from .rate_limit import RateLimitMiddleware, RATE_LIMIT_ENABLED

# Routes
from .routes import router, router_v3
from .routes_v2 import router as router_v2

__all__ = [
    # Core
    "VectorStore",
    "embedding_service",
    "ReasoningEngine",
    # Cache
    "TTLCache",
    "get_embedding_cache",
    "get_search_cache",
    "get_all_cache_stats",
    # Metrics
    "http_requests_total",
    "http_request_duration_seconds",
    "errors_total",
    "get_metrics_response",
    "normalize_path",
    # Health
    "HealthChecker",
    # Rate limiting
    "RateLimitMiddleware",
    "RATE_LIMIT_ENABLED",
    # Routes
    "router",
    "router_v2",
    "router_v3",
]
