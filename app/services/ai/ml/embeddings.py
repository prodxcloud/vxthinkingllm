"""
Embeddings and Vector Store Management
Uses sentence-transformers, FAISS, and PostgreSQL with pgvector

This module provides runtime embedding generation and vector search.
The embedding model should match the one used in precompute.py for consistency.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from .cache import (
        get_embedding_cache,
        get_search_cache,
        get_all_cache_stats,
        _normalize_query,
        _search_key,
    )
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False
    get_embedding_cache = lambda: None
    get_search_cache = lambda: None
    get_all_cache_stats = lambda: []

    def _normalize_query(q: str) -> str:
        return " ".join(q.strip().split()) if q else ""

    def _search_key(query: str, top_k: int, filter_type) -> str:
        return f"{_normalize_query(query)}|{top_k}|{filter_type or ''}"

try:
    from .metrics import (
        embedding_cache_hits,
        embedding_cache_misses,
        search_cache_hits,
        search_cache_misses,
    )
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False
    embedding_cache_hits = embedding_cache_misses = None
    search_cache_hits = search_cache_misses = None

# ============================================================================
# HARDCODED EMBEDDING MODEL CONFIGURATION
# ============================================================================
# IMPORTANT: This MUST match the model used in precompute.py!
# If you change it here, also change it in precompute.py and rebuild the index.
#
# All models are FREE from HuggingFace Hub:
#
# SMALL & FAST (recommended):
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB, 384 dim
#
# BETTER QUALITY:
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"  # 120MB, 384 dim
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"  # 420MB, 768 dim
# Alibaba-NLP/gte-Qwen2-7B-instruct, nvidia/llama-embed-nemotron-8b
# MULTILINGUAL:
# EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# ============================================================================

# Try to import pgvector support (optional)
try:
    import psycopg2
    from psycopg2.extras import execute_values
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # print("⚠️  psycopg2 not available, using FAISS only")

class VectorStore:
    """Manages embeddings, FAISS index, and vector database"""
    
    def __init__(self, data_dir: str = None, model_name: str = EMBEDDING_MODEL_NAME):
        """
        Initialize vector store
        
        Args:
            data_dir: Directory containing CSV files
            model_name: Sentence transformer model name
        """
        # Single source of truth for both input CSVs and stored artifacts:
        # va_llm_v1/app/data/
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self.model_name = model_name
        self.model = None
        self.faiss_index = None
        self.documents = []  # Store original documents
        self.metadata = []   # Store metadata for each document
        self.content_ids = [] # Store content IDs
        
        # Paths
        self.data_storage_dir = self.data_dir / "vectorstore"
        self.data_storage_dir.mkdir(exist_ok=True, parents=True)
        self.index_path = self.data_storage_dir / "faiss_index.bin"
        self.documents_path = self.data_storage_dir / "documents.pkl"
        
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        
        # Thread pool for CPU-bound operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Device selection (CUDA if available, else CPU)
        self.device = "cuda" if os.getenv("USE_CUDA", "false").lower() == "true" else "cpu"
        # print(f"🔧 Using device: {self.device}")
    
    async def initialize(self):
        """Initialize the vector store - load model, build/load index"""
        # Load sentence transformer model
        # print(f"📥 Loading sentence transformer model: {self.model_name}")
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            self.executor,
            lambda: SentenceTransformer(self.model_name, device=self.device)
        )
        
        # Get actual embedding dimension
        test_embedding = await loop.run_in_executor(
            self.executor,
            lambda: self.model.encode(["test"], convert_to_numpy=True)
        )
        self.embedding_dim = test_embedding.shape[1]
        # print(f"📏 Embedding dimension: {self.embedding_dim}")
        
        # Load or build index
        if self.index_path.exists() and self.documents_path.exists():
            # print("📂 Loading existing FAISS index...")
            await self._load_index()
        else:
            # print("🔨 New FAISS index will be created...")
            self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
            
        return True
    
    async def _load_index(self):
        """Load existing FAISS index and documents"""
        loop = asyncio.get_event_loop()
        
        # Load FAISS index
        self.faiss_index = await loop.run_in_executor(
            self.executor,
            lambda: faiss.read_index(str(self.index_path))
        )
        
        # Load documents and metadata
        if self.documents_path.exists():
            with open(self.documents_path, 'rb') as f:
                data = await loop.run_in_executor(self.executor, pickle.load, f)
                self.documents = data.get('documents', [])
                self.metadata = data.get('metadata', [])
                self.content_ids = data.get('content_ids', [])
        
        # print(f"✅ Loaded {len(self.documents)} documents from index")

    async def store_embeddings(self, texts: List[str], content_type: str, content_ids: List[str], metadata_list: List[Dict]):
        """
        Store embeddings for a batch of texts.
        Used by precompute.py
        """
        if not self.model or self.faiss_index is None:
             await self.initialize()

        if not texts:
            return 0

        # Generate embeddings
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            self.executor,
            lambda: self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        )
        
        # Add to FAISS index
        await loop.run_in_executor(
            self.executor,
            lambda: self.faiss_index.add(embeddings)
        )
        
        # Update in-memory storage
        self.documents.extend(texts)
        self.content_ids.extend(content_ids)
        
        # Enhance metadata
        for meta in metadata_list:
            meta['type'] = content_type
            self.metadata.append(meta)
            
        # Save to disk (could be optimized to not save on every batch, but safer for now)
        await self._save_index()
        
        return len(texts)

    async def _save_index(self):
        """Save index and documents to disk"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            lambda: faiss.write_index(self.faiss_index, str(self.index_path))
        )
        
        with open(self.documents_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'content_ids': self.content_ids
            }, f)

    async def get_vector_store_stats(self):
        """Get statistics about the vector store and caches."""
        out = {
            "total_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
            "by_type": {},
            "total_searches": 0,
            "avg_search_time_ms": 0,
        }
        if self.faiss_index and self.metadata:
            for m in self.metadata:
                t = m.get("type", "unknown")
                out["by_type"][t] = out["by_type"].get(t, 0) + 1
        if _CACHE_AVAILABLE:
            out["cache"] = get_all_cache_stats()
        return out

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents. Uses embedding cache (L1) and search
        result cache (L2) when enabled via VALLM_CACHE_EMBEDDINGS / VALLM_CACHE_SEARCH.
        """
        if self.faiss_index is None or not self.model:
            await self.initialize()

        if self.faiss_index is None:
            print("⚠️  FAISS index is None after initialization")
            return []

        if self.faiss_index.ntotal == 0:
            print("⚠️  FAISS index is empty (0 vectors). Run precompute.py first.")
            return []

        if not self.documents:
            print("⚠️  No documents loaded. Run precompute.py first.")
            return []

        sk = _search_key(query, top_k, filter_type)
        s_cache = get_search_cache() if _CACHE_AVAILABLE else None
        if s_cache:
            hit = s_cache.get(sk)
            if hit is not None:
                if _METRICS_AVAILABLE and search_cache_hits:
                    search_cache_hits.inc()
                return hit
            if _METRICS_AVAILABLE and search_cache_misses:
                search_cache_misses.inc()

        loop = asyncio.get_event_loop()
        nq = _normalize_query(query)
        query_embedding = None
        emb_cache = get_embedding_cache() if _CACHE_AVAILABLE else None
        if emb_cache:
            query_embedding = emb_cache.get(nq)
        if query_embedding is not None:
            if _METRICS_AVAILABLE and embedding_cache_hits:
                embedding_cache_hits.inc()
        else:
            if emb_cache and _METRICS_AVAILABLE and embedding_cache_misses:
                embedding_cache_misses.inc()
            query_embedding = await loop.run_in_executor(
                self.executor,
                lambda: self.model.encode([query], convert_to_numpy=True).astype("float32"),
            )
            if emb_cache:
                emb_cache.set(nq, query_embedding)

        k_search = top_k * 5 if filter_type else top_k
        distances, indices = await loop.run_in_executor(
            self.executor,
            lambda: self.faiss_index.search(
                query_embedding, min(k_search, self.faiss_index.ntotal)
            ),
        )

        results = []
        for _, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self.documents):
                continue
            meta = self.metadata[idx]
            if filter_type and meta.get("type") != filter_type:
                continue
            results.append({
                "document": self.documents[idx],
                "metadata": meta,
                "score": float(1 / (1 + distance)),
                "distance": float(distance),
            })
            if len(results) >= top_k:
                break

        if s_cache:
            s_cache.set(sk, results)
        return results
    
    async def get_context(
        self,
        query: str,
        top_k: int = 10
    ) -> str:
        """Get context string from search results"""
        results = await self.search(query, top_k=top_k)
        
        context_parts = []
        for i, result in enumerate(results, 1):
            doc_type = result['metadata'].get('type', 'unknown')
            context_parts.append(
                f"[{i}] {doc_type.upper()}: {result['document']}"
            )
        
        return "\n".join(context_parts)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)

# Global instance
embedding_service = VectorStore()

