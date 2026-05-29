"""
Precompute the CloudLLM vector store.

Reads files from `app/data/datasets/` (CSV, TXT, JSON, MD), embeds them with
sentence-transformers/all-MiniLM-L6-v2, and writes a FAISS index +
`documents.pkl` to `app/data/vectorstore/`.

Run from repo root:
    python -m app.services.ai.ml.precompute
    python -m app.services.ai.ml.precompute --datasets-dir app/data/datasets --vectorstore-dir app/data/vectorstore
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Iterable, List

try:
    from .embeddings import Document, VectorStore
except ImportError:
    from app.services.ai.ml.embeddings import Document, VectorStore

logger = logging.getLogger("vxcloud.precompute")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


DEFAULT_DATASETS_DIR = _repo_root() / "app" / "data" / "datasets"
DEFAULT_VECTORSTORE_DIR = _repo_root() / "app" / "data" / "vectorstore"
SUPPORTED_SUFFIXES = {".csv", ".txt", ".md", ".json"}


def _row_to_text(row: dict) -> str:
    parts = [f"{k}: {v}" for k, v in row.items() if v not in (None, "")]
    return " | ".join(parts)


def _read_csv(path: Path) -> Iterable[Document]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            text = _row_to_text(row).strip()
            if not text:
                continue
            yield Document(text=text, metadata={"source": path.name, "row": i, "type": "csv"})


def _read_text(path: Path) -> Iterable[Document]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Split on blank lines so each paragraph becomes its own retrieval unit.
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    if not chunks:
        chunks = [text.strip()] if text.strip() else []
    for i, chunk in enumerate(chunks):
        yield Document(text=chunk, metadata={"source": path.name, "chunk": i, "type": path.suffix.lstrip(".")})


def _read_json(path: Path) -> Iterable[Document]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.warning("Skipping %s (invalid JSON: %s)", path.name, e)
        return
    if isinstance(data, list):
        for i, item in enumerate(data):
            yield Document(text=json.dumps(item, ensure_ascii=False), metadata={"source": path.name, "index": i, "type": "json"})
    elif isinstance(data, dict):
        for k, v in data.items():
            yield Document(text=f"{k}: {json.dumps(v, ensure_ascii=False)}", metadata={"source": path.name, "key": k, "type": "json"})
    else:
        yield Document(text=str(data), metadata={"source": path.name, "type": "json"})


def load_documents(datasets_dir: Path) -> List[Document]:
    docs: List[Document] = []
    if not datasets_dir.exists():
        logger.error("Datasets dir does not exist: %s", datasets_dir)
        return docs

    files = sorted(p for p in datasets_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)
    logger.info("Found %d files in %s", len(files), datasets_dir)
    for path in files:
        suffix = path.suffix.lower()
        try:
            if suffix == ".csv":
                file_docs = list(_read_csv(path))
            elif suffix == ".json":
                file_docs = list(_read_json(path))
            else:
                file_docs = list(_read_text(path))
        except Exception as e:
            logger.warning("Skipping %s: %s", path.name, e)
            continue
        logger.info("  %s → %d documents", path.name, len(file_docs))
        docs.extend(file_docs)
    return docs


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the CloudLLM FAISS vectorstore.")
    parser.add_argument("--datasets-dir", type=Path, default=DEFAULT_DATASETS_DIR)
    parser.add_argument("--vectorstore-dir", type=Path, default=DEFAULT_VECTORSTORE_DIR)
    args = parser.parse_args(argv)

    logger.info("Datasets dir:    %s", args.datasets_dir)
    logger.info("Vectorstore dir: %s", args.vectorstore_dir)

    docs = load_documents(args.datasets_dir)
    if not docs:
        logger.error("No documents found. Add CSV/TXT/JSON/MD files under %s", args.datasets_dir)
        return 1

    logger.info("Embedding %d documents…", len(docs))
    vs = VectorStore(vectorstore_dir=args.vectorstore_dir)
    total = vs.build(docs)
    logger.info("Done. %d vectors written to %s", total, args.vectorstore_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
