"""
VaLLM Precompute Script - Build FAISS Index from CSV Data

This script reads all CSVs from app/data/*.csv, generates embeddings using
sentence-transformers, and saves a FAISS index to app/data/vectorstore/.

QUICK START (run from va_llm_v1 root directory):
================================================

    # Build the FAISS index
    python ./app/precompute.py

    # Then train the LLM (optional)
    python ./app/train.py --num-train-epochs 1

    # Start the FastAPI server
    python -m app.app

OUTPUT:
=======
    app/data/vectorstore/
        faiss_index.bin    - FAISS vector index
        documents.pkl      - Original documents + metadata
"""

import argparse
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

try:
    import PyPDF2
    HAVE_PDF = True
except ImportError:
    HAVE_PDF = False

# ============================================================================
# HARDCODED EMBEDDING MODEL CONFIGURATION
# ============================================================================
# All models below are FREE and hosted on HuggingFace Hub.
# They are downloaded automatically on first run.
#
# SMALL & FAST (recommended for local dev):
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB, 384 dim, FAST
#
# BETTER QUALITY (still reasonable size):
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"  # 120MB, 384 dim
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB, 384 dim, FAST
# 
# MULTILINGUAL (if you have non-English data):
# EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 470MB
# openai/gpt-oss-120b
# LARGE & HIGH QUALITY (for production):
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-roberta-large-v1"  # 1.4GB, 1024 dim
#
# ============================================================================
# MODEL COMPARISON:
# ============================================================================
# | Model                          | Size  | Dim | Speed  | Quality |
# |--------------------------------|-------|-----|--------|---------|
# | all-MiniLM-L6-v2 (default)     | 80MB  | 384 | Fast   | Good    |
# | all-MiniLM-L12-v2              | 120MB | 384 | Medium | Better  |
# | all-mpnet-base-v2              | 420MB | 768 | Medium | Best    |
# | paraphrase-multilingual-MiniLM | 470MB | 384 | Medium | Good    |
# | all-roberta-large-v1           | 1.4GB | 1024| Slow   | Best    |
# ============================================================================


def row_to_text(row: Dict[str, Any]) -> str:
    # Convert one CSV row into a single textual document.
    # This is what we will embed and later retrieve via FAISS.
    parts: List[str] = []
    for k, v in row.items():
        if v is None:
            continue
        sv = str(v)
        if sv.strip() == "" or sv.strip().lower() == "nan":
            continue
        parts.append(f"{k}: {sv}")
    return " | ".join(parts)


def build_faiss_index(embeddings: np.ndarray, use_cosine: bool) -> faiss.Index:
    # Build a FAISS index from a (N, D) float32 embedding matrix.
    if embeddings.ndim != 2:
        raise ValueError(f"Expected 2D embeddings, got shape={embeddings.shape}")

    dim = embeddings.shape[1]

    # The running FastAPI app's VectorStore assumes L2 distances.
    # Keep the index metric consistent so scoring remains correct.
    index = faiss.IndexFlatL2(dim)

    index.add(embeddings)
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="Precompute sentence-transformer embeddings and build a FAISS index")

    parser.add_argument(
        "--dataset",
        type=str,
        default=str(Path("app") / "data" / "container_operations.csv"),
        help="Primary CSV dataset (used first if --dataset-dir is set)",
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(Path("app") / "data"),
        help="If set, embed all CSVs in this folder (recommended)",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=EMBEDDING_MODEL_NAME,
        help=f"SentenceTransformer model name. Default: {EMBEDDING_MODEL_NAME}",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path("app") / "data" / "vectorstore"),
        help="Directory where faiss_index.bin and documents.pkl will be written",
    )
    parser.add_argument("--batch-size", type=int, default=128)

    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else None
    if dataset_dir is None:
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    else:
        if not dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================================================
    # STEP 1: DISCOVER AND LOAD CSV FILES
    # ==========================================================================
    print("\n" + "=" * 70)
    print("VaLLM PRECOMPUTE - Building FAISS Vector Index")
    print("=" * 70)

    if dataset_dir is not None:
        csv_paths = sorted(p for p in dataset_dir.glob("*.csv") if p.is_file())
        if not csv_paths:
            raise FileNotFoundError(f"No CSV files found in: {dataset_dir}")

        if dataset_path.exists():
            csv_paths = [dataset_path] + [p for p in csv_paths if p.resolve() != dataset_path.resolve()]

        print(f"\n[DIR] Found {len(csv_paths)} CSV file(s) in {dataset_dir}:")
        print("-" * 50)

        frames = []
        total_rows = 0
        for idx, p in enumerate(csv_paths, 1):
            try:
                print(f"\n[{idx}/{len(csv_paths)}] Processing: {p.name}")
                frame = pd.read_csv(p, on_bad_lines='warn')
                row_count = len(frame)
                col_count = len(frame.columns)
                total_rows += row_count
                print(f"    [OK] Loaded {row_count} rows x {col_count} columns")
                print(f"    Columns: {', '.join(frame.columns[:5])}{'...' if col_count > 5 else ''}")
                frames.append(frame)
            except Exception as e:
                print(f"    [WARN] Could not parse: {e}")
                continue

        if not frames:
            raise FileNotFoundError(f"No valid CSV files could be parsed in: {dataset_dir}")

        df = pd.concat(frames, ignore_index=True)
        dataset_for_metadata = str(dataset_dir)

        print(f"\n{'='*50}")
        print(f"TOTAL: {total_rows} rows from {len(frames)} file(s)")
        print(f"{'='*50}")
    else:
        print(f"\n[FILE] Processing single file: {dataset_path}")
        df = pd.read_csv(dataset_path, on_bad_lines='warn')
        print(f"    [OK] Loaded {len(df)} rows x {len(df.columns)} columns")
        dataset_for_metadata = str(dataset_path)

    if len(df) == 0:
        raise ValueError(f"Dataset is empty: {dataset_for_metadata}")

    # ==========================================================================
    # STEP 2: CONVERT ROWS TO TEXT
    # ==========================================================================
    print(f"\n[STEP 2] Converting rows to text documents...")
    print("-" * 50)

    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    skipped = 0

    for i, row in df.iterrows():
        row_dict = row.to_dict()
        text = row_to_text(row_dict)
        if not text.strip():
            skipped += 1
            continue

        texts.append(text)
        metadatas.append(
            {
                "id": int(i),
                "text": text,
                "source": str(dataset_path),
                "raw": {str(k): ("" if pd.isna(v) else str(v)) for k, v in row_dict.items()},
            }
        )

        # Progress indicator every 50 rows
        if (i + 1) % 50 == 0:
            print(f"    [OK] Processed {i + 1} rows...")

    print(f"\n    [OK] Converted {len(texts)} rows to text documents")
    if skipped > 0:
        print(f"    [WARN] Skipped {skipped} empty rows")

    # ==========================================================================
    # STEP 2b: PROCESS PDF FILES
    # ==========================================================================
    if dataset_dir:
        pdf_paths = sorted(p for p in dataset_dir.glob("*.pdf") if p.is_file())

        if pdf_paths:
            print(f"\n[STEP 2b] Processing {len(pdf_paths)} PDF files...")
            print("-" * 50)

            if not HAVE_PDF:
                print("    [WARN] Found .pdf files but 'PyPDF2' is not installed.")
                print("    Run: pip install PyPDF2")
            else:
                pdf_docs_count = 0
                for p in pdf_paths:
                    try:
                        print(f"    Processing: {p.name}")
                        reader = PyPDF2.PdfReader(p)
                        for page_num, page in enumerate(reader.pages):
                            text = page.extract_text()
                            if not text or not text.strip():
                                continue

                            # clean up text slightly
                            clean_text = text.strip()

                            # Add to global lists
                            texts.append(clean_text)
                            metadatas.append({
                                "id": f"{p.name}_p{page_num+1}",
                                "text": clean_text,
                                "source": str(p),
                                "raw": {"page": page_num + 1, "file": p.name}
                            })
                            pdf_docs_count += 1
                    except Exception as e:
                        print(f"    [ERROR] Error reading {p.name}: {e}")

                print(f"    [OK] Extracted {pdf_docs_count} pages from PDFs")

    # ==========================================================================
    # STEP 3: LOAD EMBEDDING MODEL
    # ==========================================================================
    print(f"\n[STEP 3] Loading embedding model...")
    print("-" * 50)
    print(f"    Model: {args.embedding_model}")

    model = SentenceTransformer(args.embedding_model)

    # Check device
    device = "cuda" if model.device.type == "cuda" else "cpu"
    print(f"    Device: {device.upper()}")
    print(f"    [OK] Model loaded successfully!")

    # ==========================================================================
    # STEP 4: GENERATE EMBEDDINGS
    # ==========================================================================
    print(f"\n[STEP 4] Generating embeddings for {len(texts)} documents...")
    print("-" * 50)
    print(f"    Batch size: {args.batch_size}")
    print(f"    Embedding dimension: {model.get_sentence_embedding_dimension()}")
    print(f"\n    Encoding documents (this may take a moment)...")

    import time
    start_time = time.time()

    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=False,
    ).astype(np.float32)

    elapsed = time.time() - start_time
    print(f"\n    [OK] Generated {len(embeddings)} embeddings in {elapsed:.2f} seconds")
    print(f"    Embedding shape: {embeddings.shape}")

    # ==========================================================================
    # STEP 5: BUILD FAISS INDEX
    # ==========================================================================
    print(f"\n[STEP 5] Building FAISS index...")
    print("-" * 50)

    index = build_faiss_index(embeddings, use_cosine=False)

    print(f"    [OK] FAISS index built with {index.ntotal} vectors")
    print(f"    Vector dimension: {index.d}")

    # ==========================================================================
    # STEP 6: SAVE TO DISK
    # ==========================================================================
    print(f"\n[STEP 6] Saving to disk...")
    print("-" * 50)

    index_path = out_dir / "faiss_index.bin"
    documents_path = out_dir / "documents.pkl"

    faiss.write_index(index, str(index_path))
    print(f"    [OK] FAISS index saved: {index_path}")

    with documents_path.open("wb") as f:
        pickle.dump(
            {
                "documents": texts,
                "metadata": metadatas,
                "content_ids": [str(m.get("id")) for m in metadatas],
            },
            f,
        )
    print(f"    [OK] Documents saved: {documents_path}")
    
    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print(f"\n{'='*70}")
    print("PRECOMPUTE COMPLETE!")
    print("=" * 70)
    print(f"""
    Summary:
    -----------------------------------------
    CSV files processed  : {len(frames) if 'frames' in dir() else 1}
    Documents indexed    : {len(texts)}
    Vectors created      : {index.ntotal}
    Vector dimension     : {index.d}
    Total time           : {elapsed:.2f} seconds

    Output files:
    -----------------------------------------
    FAISS Index  : {index_path}
    Documents    : {documents_path}

    [OK] Ready! Run 'python -m app.app' to start the server.
    """)


if __name__ == "__main__":
    main()
