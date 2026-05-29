"""
Embeddings + FAISS vector store for the CloudLLM.

Loads sentence-transformers/all-MiniLM-L6-v2 and persists a FAISS L2 index
plus a pickled `documents.pkl` (text + metadata) under `app/data/vectorstore/`.

Usage:
    vs = VectorStore()
    await vs.initialize()                # loads model + index if present
    results = await vs.search("query", top_k=5)
"""

from __future__ import annotations

import asyncio
import logging
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("vxcloud.embeddings")

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _vectorstore_dir() -> Path:
    """`<repo>/app/data/vectorstore` — repo root resolved relative to this file."""
    return Path(__file__).resolve().parents[3] / "data" / "vectorstore"


@dataclass
class Document:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingService:
    """Thin wrapper around sentence-transformers. Lazy-loads the model."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        model = self._load()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=False,
        )
        return vectors.astype("float32")

    @property
    def dimension(self) -> int:
        model = self._load()
        return int(model.get_sentence_embedding_dimension())


embedding_service = EmbeddingService()


class VectorStore:
    """FAISS L2 index + pickled document list."""

    def __init__(self, vectorstore_dir: Optional[Path] = None, embedding: Optional[EmbeddingService] = None):
        self.dir = Path(vectorstore_dir) if vectorstore_dir else _vectorstore_dir()
        self.embedding = embedding or embedding_service
        self.index = None
        self.documents: List[Document] = []

    @property
    def index_path(self) -> Path:
        return self.dir / "faiss_index.bin"

    @property
    def documents_path(self) -> Path:
        return self.dir / "documents.pkl"

    async def initialize(self) -> None:
        await asyncio.to_thread(self._load_from_disk)

    def _load_from_disk(self) -> None:
        import faiss
        if not self.index_path.exists() or not self.documents_path.exists():
            logger.info("Vectorstore not on disk yet (%s)", self.dir)
            return
        self.index = faiss.read_index(str(self.index_path))
        with open(self.documents_path, "rb") as f:
            self.documents = pickle.load(f)
        logger.info("Loaded vectorstore: %d vectors", self.index.ntotal)

    def build(self, documents: List[Document]) -> int:
        import faiss
        if not documents:
            raise ValueError("No documents to index")

        texts = [d.text for d in documents]
        vectors = self.embedding.encode(texts)
        if vectors.ndim != 2:
            raise ValueError(f"expected 2D vectors, got shape {vectors.shape}")

        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(vectors)

        self.dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_path))
        with open(self.documents_path, "wb") as f:
            pickle.dump(documents, f)

        self.index = index
        self.documents = documents
        logger.info("Wrote %d vectors → %s", index.ntotal, self.dir)
        return index.ntotal

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None or not self.documents:
            return []
        vector = await asyncio.to_thread(self.embedding.encode, [query])
        distances, indices = await asyncio.to_thread(self.index.search, vector, top_k)
        results: List[Dict[str, Any]] = []
        for dist, idx in zip(distances[0].tolist(), indices[0].tolist()):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            results.append({"document": doc.text, "score": float(dist), "metadata": doc.metadata})
        return results

    async def get_vector_store_stats(self) -> Dict[str, Any]:
        return {
            "total_vectors": int(self.index.ntotal) if self.index is not None else 0,
            "documents": len(self.documents),
            "dir": str(self.dir),
            "embedding_model": self.embedding.model_name,
        }

    async def cleanup(self) -> None:
        self.index = None
        self.documents = []
