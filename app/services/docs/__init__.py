"""Docs-grounded Q&A for vxcloud.io (crawl -> BM25 index -> grounded answer).

Deliberately free of torch/transformers imports: the LLM is injected as a callable.
"""

from .answer import NOT_FOUND, answer
from .crawler import DEFAULT_SITES, Chunk, crawl, crawl_sites, html_to_chunks
from .index import DocIndex
from .routes import router
from .service import DocsService

__all__ = ["Chunk", "DEFAULT_SITES", "DocIndex", "DocsService", "NOT_FOUND", "answer",
           "crawl", "crawl_sites", "html_to_chunks", "router"]
