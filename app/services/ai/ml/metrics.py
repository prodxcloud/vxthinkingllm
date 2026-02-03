"""
Prometheus Metrics for VaLLM
Exposes metrics at /metrics endpoint
"""
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from fastapi import Response
import time
from typing import Optional

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

# Business Metrics
vector_search_requests = Counter(
    'vector_search_requests_total',
    'Total vector search requests',
    ['status']
)

vector_search_duration = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Cache metrics (embedding L1, search L2)
embedding_cache_hits = Counter(
    'embedding_cache_hits_total',
    'Embedding cache hits'
)
embedding_cache_misses = Counter(
    'embedding_cache_misses_total',
    'Embedding cache misses'
)
search_cache_hits = Counter(
    'search_cache_hits_total',
    'Search result cache hits'
)
search_cache_misses = Counter(
    'search_cache_misses_total',
    'Search result cache misses'
)

llm_generation_requests = Counter(
    'llm_generation_requests_total',
    'Total LLM generation requests',
    ['model', 'status']
)

llm_generation_tokens = Counter(
    'llm_generation_tokens_total',
    'Total tokens generated',
    ['model']
)

llm_generation_duration = Histogram(
    'llm_generation_duration_seconds',
    'LLM generation duration',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# System Metrics
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

vector_store_size = Gauge(
    'vector_store_size',
    'Number of vectors in store'
)

model_loaded = Gauge(
    'model_loaded',
    'Whether model is loaded (1=yes, 0=no)',
    ['model_name']
)

# Error Metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Performance Metrics
reasoning_steps_total = Counter(
    'reasoning_steps_total',
    'Total reasoning steps executed',
    ['step_type']
)

reasoning_duration = Summary(
    'reasoning_duration_seconds',
    'Reasoning engine duration'
)


def get_metrics_response() -> Response:
    """Get Prometheus metrics as HTTP response"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def normalize_path(path: str) -> str:
    """Normalize path for metrics (remove IDs)"""
    import re
    # Replace UUIDs and IDs with placeholders
    path = re.sub(r'/[a-f0-9]{8}-[a-f0-9-]+', '/:uuid', path)
    path = re.sub(r'/\d+', '/:id', path)
    return path
