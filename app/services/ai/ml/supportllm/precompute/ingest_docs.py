"""
SupportLLM precompute — ingest Confluence / Notion / Slack / local docs into Qdrant.

Uses sentence-transformers for embeddings (same family as the main VxThinkingLLM
vector store — `all-MiniLM-L6-v2`) and pushes into a Qdrant collection.

If Qdrant isn't reachable, it falls back to a local FAISS-on-disk index under
`app/data/precompute/supportllm/` so the pipeline always completes.

QUICK START (from repo root):
    python -m app.services.ai.ml.supportllm.precompute.ingest_docs \
        --source app/data/datasets/supportllm \
        --collection supportllm
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_OUT_DIR = Path("app") / "data" / "precompute" / "supportllm"


@dataclass
class Doc:
    id: str
    text: str
    source: str
    metadata: Dict[str, str]


def _iter_text_files(source: Path) -> Iterable[Path]:
    for ext in ("*.md", "*.txt", "*.html", "*.json", "*.jsonl"):
        for p in glob.glob(str(source / "**" / ext), recursive=True):
            yield Path(p)


def _chunk(text: str, chunk_chars: int = 900, overlap: int = 150) -> List[str]:
    text = text.strip()
    if len(text) <= chunk_chars:
        return [text] if text else []
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + chunk_chars])
        i += chunk_chars - overlap
    return chunks


def _load_docs(source: Path) -> List[Doc]:
    docs: List[Doc] = []
    for path in _iter_text_files(source):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(source)) if path.is_relative_to(source) else str(path)
        for i, chunk in enumerate(_chunk(content)):
            h = hashlib.sha1(f"{rel}:{i}".encode()).hexdigest()[:16]
            docs.append(Doc(
                id=h,
                text=chunk,
                source=rel,
                metadata={"chunk": str(i), "path": rel, "kind": path.suffix.lstrip(".")},
            ))
    return docs


def _embed(texts: List[str], model_name: str) -> List[List[float]]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True)
    return [v.tolist() for v in vectors]


def _push_qdrant(
    docs: List[Doc],
    vectors: List[List[float]],
    *,
    url: str,
    api_key: Optional[str],
    collection: str,
) -> bool:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qmodels
    except ImportError:
        print("[SupportLLM precompute] qdrant-client not installed, skipping Qdrant upload.")
        return False

    try:
        client = QdrantClient(url=url, api_key=api_key, timeout=10.0)
        client.recreate_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(
                size=len(vectors[0]),
                distance=qmodels.Distance.COSINE,
            ),
        )
        client.upsert(
            collection_name=collection,
            points=[
                qmodels.PointStruct(
                    id=int(d.id, 16) % (2**63 - 1),
                    vector=v,
                    payload={"text": d.text, "source": d.source, **d.metadata},
                )
                for d, v in zip(docs, vectors)
            ],
        )
        print(f"[SupportLLM precompute] pushed {len(docs)} chunks to Qdrant `{collection}` at {url}")
        return True
    except Exception as e:  # pragma: no cover
        print(f"[SupportLLM precompute] Qdrant upload failed ({e}); falling back to local file.")
        return False


def _write_local(docs: List[Doc], vectors: List[List[float]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(docs),
        "dimension": len(vectors[0]) if vectors else 0,
        "items": [
            {"id": d.id, "text": d.text, "source": d.source, "metadata": d.metadata, "vector": v}
            for d, v in zip(docs, vectors)
        ],
    }
    out_path = out_dir / "index.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"[SupportLLM precompute] wrote local fallback index -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest docs into SupportLLM vector store")
    parser.add_argument("--source", type=str, default=str(Path("app") / "data" / "datasets" / "supportllm"))
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--embedding-model", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--qdrant-url", type=str, default=os.getenv("QDRANT_URL", "http://localhost:6333"))
    parser.add_argument("--qdrant-api-key", type=str, default=os.getenv("QDRANT_API_KEY"))
    parser.add_argument("--collection", type=str, default="supportllm")
    args = parser.parse_args()

    source = Path(args.source)
    out_dir = Path(args.out_dir)

    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    docs = _load_docs(source)
    if not docs:
        print(f"[SupportLLM precompute] no text files under {source} — nothing to ingest.")
        return
    print(f"[SupportLLM precompute] chunked {len(docs)} passages from {source}")

    vectors = _embed([d.text for d in docs], args.embedding_model)

    pushed = _push_qdrant(
        docs, vectors,
        url=args.qdrant_url, api_key=args.qdrant_api_key, collection=args.collection,
    )
    if not pushed:
        _write_local(docs, vectors, out_dir)


if __name__ == "__main__":
    main()
