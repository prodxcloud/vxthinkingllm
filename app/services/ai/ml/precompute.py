"""
VaLLM Precompute Script - Build FAISS Index from Multi-Format Data (ThinkingLLM)

This script reads all supported files from app/data/datasets/thinkingllm/ and
generates embeddings using sentence-transformers, saving a FAISS index to
app/data/precompute/thinkingllm/.

SUPPORTED FORMATS:
==================
    - CSV   (.csv)           - Tabular data with headers
    - JSON  (.json)          - Arrays of objects, nested structures
    - TXT   (.txt)           - Plain text files (chunked into sections)
    - PDF   (.pdf)           - PDF documents (page-by-page extraction)
    - SQL   (.sql)           - SQL files (CREATE TABLE, INSERT, comments)
    - Excel (.xlsx, .xls)    - Excel spreadsheets (all sheets)

QUICK START (run from va_llm_v1 root directory):
================================================

    # Build the FAISS index
    python ./app/precompute.py

    # Then train the LLM (optional)
    python ./app/train.py --num-train-epochs 1

    # Start the FastAPI server
    python -m app.app

INPUT (datasets):  app/data/datasets/thinkingllm/  (*.csv, *.json, *.txt, *.pdf, *.sql, *.xlsx, *.xls)
OUTPUT:
=======
    app/data/precompute/thinkingllm/
        faiss_index.bin    - FAISS vector index (IndexFlatIP, cosine similarity)
        documents.pkl      - Original documents + metadata
"""

import argparse
import json
import pickle
import re
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

try:
    import openpyxl  # noqa: F401
    HAVE_EXCEL = True
except ImportError:
    HAVE_EXCEL = False

# ============================================================================
# EMBEDDING MODEL - Must match embeddings.py at runtime
# Choose a sentence-transformers model optimized for semantic similarity.
# These work well for DevOps agents retrieving logs, docs, commands, runbooks.
# ============================================================================

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# ⭐ Most common default. Very fast, ~80MB, 384-dim. Good balance of speed and accuracy.

# Other options (uncomment ONE to switch, and update embeddings.py to match):
# EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"   # ~120MB, higher quality
# EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-MiniLM-L3-v2"  # ~60MB, fastest
# EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # multilingual
# EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # ~100MB, strong RAG quality
# EMBEDDING_MODEL_NAME = "roneneldan/TinyStories-1M"  # DO NOT USE - causal LM, OOM on CPU

# ============================================================================


def row_to_text(row: Dict[str, Any]) -> str:
    """
    Convert one CSV row into text for embedding.

    For cloud_deployments rows (has 'prompt' + 'intent'):
      Use the prompt as primary text plus intent and key discriminating fields.
      This keeps embeddings focused so "deploy ec2 instance" matches provision_vm
      training data, not random provision_docker rows.

    For other rows (non-deployment CSVs):
      Use description/category or concatenate non-empty fields.

    The FULL row is always stored in metadata.raw for payload generation.
    """
    prompt = _clean(row.get("prompt"))
    intent = _clean(row.get("intent"))

    # Deployment rows: prompt-focused embedding
    if prompt and intent:
        parts = [prompt, f"intent: {intent}"]

        # Pull the executable command out of `path` (raw column) AND/OR
        # `action_json.command` so semantic search can match on command
        # similarity, not just prompt phrasing.
        path_val = _clean(row.get("path"))
        if path_val:
            parts.append(f"command: {path_val}")
        action_json_raw = _clean(row.get("action_json"))
        if action_json_raw:
            try:
                aj = json.loads(action_json_raw)
                aj_cmd = _clean(aj.get("command")) or _clean(aj.get("path"))
                if aj_cmd and aj_cmd != path_val:
                    parts.append(f"command: {aj_cmd}")
                aj_explanation = _clean(aj.get("explanation"))
                if aj_explanation:
                    parts.append(f"explanation: {aj_explanation}")
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass  # action_json may not be valid JSON in some rows; ignore

        # Add key fields per intent type to sharpen discrimination
        for field in ("instance_type", "cloud_provider", "region", "os",
                      "cluster_name", "node_count", "node_type", "kubernetes_version",
                      "docker_image", "container_name", "ports",
                      "database_engine", "database_name",
                      "app_name", "app_port",
                      "server_name", "http_port",
                      "tags", "category"):
            val = _clean(row.get(field))
            if val:
                parts.append(f"{field}: {val}")
        return " | ".join(parts)

    # Non-deployment rows: use description or full row
    desc = _clean(row.get("description"))
    category = _clean(row.get("category"))
    if desc:
        parts = []
        if category:
            parts.append(f"category: {category}")
        parts.append(desc)
        resolution = _clean(row.get("resolution_or_recommendation"))
        if resolution:
            parts.append(f"resolution: {resolution}")
        return " | ".join(parts)

    # Fallback: all non-empty fields
    parts: List[str] = []
    for k, v in row.items():
        val = _clean(v)
        if val:
            parts.append(f"{k}: {val}")
    return " | ".join(parts)


def _clean(v: Any) -> str:
    """Return cleaned string or empty string for None/NaN."""
    if v is None:
        return ""
    sv = str(v).strip()
    if sv.lower() in ("", "nan"):
        return ""
    return sv


def load_json_rows(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON file and return list of row dicts for embedding.

    Supports:
    - deployments.json: object with "use_cases" array (prompt, intent, payload, etc.)
    - Other JSON: array of objects, or dict with nested keys (use_cases, data, items, etc.)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    if isinstance(data, list):
        for item in data:
            rows.append(item if isinstance(item, dict) else {"content": str(item), "source": file_path.name})
        return rows

    if not isinstance(data, dict):
        return rows

    # deployments.json-style: { "metadata": {...}, "use_cases": [ {...}, ... ] }
    if "use_cases" in data and isinstance(data["use_cases"], list):
        for item in data["use_cases"]:
            if isinstance(item, dict):
                rows.append(item)
        return rows

    # Other nested structures (deployment/provisioning: use_cases, data, items)
    nested_keys = [
        "use_cases", "deployments", "records", "data", "items", "entries",
    ]
    for key in nested_keys:
        if key in data and isinstance(data[key], list):
            for item in data[key]:
                if isinstance(item, dict):
                    item = {**item, "_category": key, "_source": file_path.name}
                    rows.append(item)
                else:
                    rows.append({"content": str(item), "category": key, "source": file_path.name})
            return rows

    # Single object: treat as one record
    flat = {"_source": file_path.name}
    for k, v in data.items():
        if isinstance(v, (dict, list)):
            flat[k] = str(v)
        else:
            flat[k] = v
    rows.append(flat)
    return rows


def load_txt_rows(file_path: Path, chunk_size: int = 1000) -> List[Dict[str, Any]]:
    """Load TXT file and chunk into embedding-ready row dicts.

    Splits by section headers, then paragraphs, then fixed chunk size.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    rows: List[Dict[str, Any]] = []

    # Split by markdown-style headers or SECTION markers
    header_pattern = r'\n(?=(?:SECTION|#{1,3}|[A-Z][A-Z\s]+:))'
    parts = re.split(header_pattern, content)
    sections = [p.strip() for p in parts if len(p.strip()) > 50]

    # Fallback: paragraphs
    if len(sections) <= 1:
        paragraphs = content.split("\n\n")
        sections = [p.strip() for p in paragraphs if len(p.strip()) > 50]

    # Fallback: fixed chunks
    if len(sections) <= 1 and len(content) > chunk_size:
        sections = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]
            if chunk.strip():
                sections.append(chunk.strip())

    for i, section in enumerate(sections):
        rows.append({
            "content": section,
            "source": file_path.name,
            "section_index": i + 1,
            "total_sections": len(sections),
        })
    return rows


def load_pdf_rows(file_path: Path) -> List[Dict[str, Any]]:
    """Load PDF file page-by-page into embedding-ready row dicts."""
    if not HAVE_PDF:
        print(f"    [WARN] PyPDF2 not installed, skipping {file_path.name}")
        return []

    reader = PyPDF2.PdfReader(file_path)
    rows: List[Dict[str, Any]] = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            rows.append({
                "content": text.strip(),
                "source": file_path.name,
                "page": page_num + 1,
            })
    return rows


def load_sql_rows(file_path: Path) -> List[Dict[str, Any]]:
    """Load SQL file and extract meaningful statements for embedding.

    Parses CREATE TABLE, INSERT, and block comments as separate documents.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    rows: List[Dict[str, Any]] = []

    # Extract block comments (often contain documentation)
    block_comments = re.findall(r'/\*\*(.*?)\*/', content, re.DOTALL)
    for i, comment in enumerate(block_comments):
        text = comment.strip().lstrip("*").strip()
        if len(text) > 30:
            rows.append({
                "content": text,
                "source": file_path.name,
                "sql_type": "comment",
                "index": i + 1,
            })

    # Extract individual SQL statements
    statements = re.split(r';\s*\n', content)
    for i, stmt in enumerate(statements):
        stmt = stmt.strip()
        if not stmt or len(stmt) < 20:
            continue
        # Remove inline comments for cleaner text
        clean = re.sub(r'--.*$', '', stmt, flags=re.MULTILINE).strip()
        if not clean:
            continue

        # Classify statement type
        upper = clean.upper().lstrip()
        if upper.startswith("CREATE TABLE"):
            sql_type = "create_table"
        elif upper.startswith("CREATE INDEX"):
            sql_type = "create_index"
        elif upper.startswith("INSERT"):
            sql_type = "insert"
        elif upper.startswith("ALTER"):
            sql_type = "alter"
        elif upper.startswith("CREATE VIEW"):
            sql_type = "create_view"
        elif upper.startswith("CREATE FUNCTION") or upper.startswith("CREATE PROCEDURE"):
            sql_type = "function"
        else:
            sql_type = "statement"

        rows.append({
            "content": clean,
            "source": file_path.name,
            "sql_type": sql_type,
            "index": i + 1,
        })
    return rows


def load_excel_rows(file_path: Path) -> List[Dict[str, Any]]:
    """Load Excel file (.xlsx/.xls) — all sheets — into row dicts."""
    if not HAVE_EXCEL:
        print(f"    [WARN] openpyxl not installed, skipping {file_path.name}")
        return []

    rows: List[Dict[str, Any]] = []
    xls = pd.ExcelFile(file_path)
    for sheet_name in xls.sheet_names:
        frame = pd.read_excel(xls, sheet_name=sheet_name)
        if frame.empty:
            continue
        for _, row in frame.iterrows():
            row_dict = row.to_dict()
            row_dict["_sheet"] = sheet_name
            row_dict["_source"] = file_path.name
            rows.append(row_dict)
    return rows


def use_case_to_row(uc: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a deployments.json use_case so row_to_text() can use it (prompt, intent, payload fields)."""
    row = {
        "prompt": uc.get("prompt"),
        "intent": uc.get("intent"),
        "deployment_id": uc.get("deployment_id"),
        "endpoint_url": uc.get("endpoint_url"),
    }
    payload = uc.get("payload") or {}
    if isinstance(payload, dict):
        row.update(payload)
    return row


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """Build a FAISS IndexFlatIP index from normalized embeddings (cosine similarity)."""
    if embeddings.ndim != 2:
        raise ValueError(f"Expected 2D embeddings, got shape={embeddings.shape}")

    dim = embeddings.shape[1]

    # Normalize for cosine similarity via Inner Product
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="Precompute sentence-transformer embeddings and build a FAISS index")

    parser.add_argument(
        "--dataset",
        type=str,
        default=str(Path("app") / "data" / "datasets" / "thinkingllm" / "cloud_deployments.csv"),
        help="Primary dataset file (used first if --dataset-dir is set)",
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(Path("app") / "data" / "datasets" / "thinkingllm"),
        help="If set, embed all supported files in this folder (recommended)",
    )
    parser.add_argument(
        "--file-types",
        type=str,
        default="csv,json,txt,md,pdf,sql,xlsx,xls",
        help="Comma-separated list of file types to include (default: csv,json,txt,md,pdf,sql,xlsx,xls)",
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
        default=str(Path("app") / "data" / "precompute" / "thinkingllm"),
        help="Directory where faiss_index.bin and documents.pkl will be written",
    )
    parser.add_argument("--batch-size", type=int, default=128)

    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else None
    file_types = [ft.strip().lower() for ft in args.file_types.split(",")]

    if dataset_dir is None:
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    else:
        if not dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================================================
    # STEP 1: DISCOVER AND LOAD ALL SUPPORTED FILES
    # ==========================================================================
    print("\n" + "=" * 70)
    print("VaLLM PRECOMPUTE - Building FAISS Vector Index")
    print("=" * 70)

    # Collect (row_dict, source_path, is_json_use_case) for unified processing
    all_rows: List[tuple] = []  # (row_dict, source_str, is_json_use_case)
    file_counts: Dict[str, int] = {}

    def _skip_non_provisioning(path: Path) -> bool:
        name = path.name.lower()
        return "observability" in name or "troubleshoot" in name or "incident" in name

    def _glob_type(directory: Path, ext: str) -> List[Path]:
        return sorted(p for p in directory.glob(f"*.{ext}") if p.is_file() and not _skip_non_provisioning(p))

    if dataset_dir is not None:
        # Discover files by type
        files_by_type: Dict[str, List[Path]] = {}
        for ft in file_types:
            paths = _glob_type(dataset_dir, ft)
            if paths:
                files_by_type[ft] = paths

        if not files_by_type:
            raise FileNotFoundError(f"No supported files ({', '.join(file_types)}) found in: {dataset_dir}")

        total_files = sum(len(v) for v in files_by_type.values())
        print(f"\n[DIR] Found {total_files} file(s) in {dataset_dir}:")
        for ft, paths in files_by_type.items():
            print(f"    {ft.upper():5s}: {len(paths)} file(s)")
        print("-" * 50)

        global_idx = 0

        # --- CSV ---
        if "csv" in files_by_type:
            csv_paths = files_by_type["csv"]
            # Ensure primary CSV is first
            if dataset_path.exists() and dataset_path.suffix.lower() == ".csv":
                csv_paths = [dataset_path] + [p for p in csv_paths if p.resolve() != dataset_path.resolve()]
            for p in csv_paths:
                global_idx += 1
                try:
                    print(f"\n[{global_idx}/{total_files}] CSV: {p.name}")
                    frame = pd.read_csv(p, on_bad_lines='warn', engine='python', quotechar='"')
                    file_counts["csv"] = file_counts.get("csv", 0) + 1
                    print(f"    [OK] Loaded {len(frame)} rows x {len(frame.columns)} columns")
                    for _, row in frame.iterrows():
                        all_rows.append((row.to_dict(), str(p), False))
                except Exception as e:
                    print(f"    [WARN] Could not parse: {e}")

        # --- JSON ---
        if "json" in files_by_type:
            for p in files_by_type["json"]:
                global_idx += 1
                try:
                    print(f"\n[{global_idx}/{total_files}] JSON: {p.name}")
                    rows = load_json_rows(p)
                    file_counts["json"] = file_counts.get("json", 0) + 1
                    print(f"    [OK] Loaded {len(rows)} record(s)")
                    use_cases_format = len(rows) > 0 and isinstance(rows[0], dict) and "prompt" in rows[0] and "intent" in rows[0]
                    for row in rows:
                        all_rows.append((row, str(p), bool(use_cases_format and isinstance(row, dict) and "prompt" in row)))
                except Exception as e:
                    print(f"    [WARN] Could not parse: {e}")

        # --- TXT ---
        if "txt" in files_by_type:
            for p in files_by_type["txt"]:
                global_idx += 1
                try:
                    print(f"\n[{global_idx}/{total_files}] TXT: {p.name}")
                    rows = load_txt_rows(p)
                    file_counts["txt"] = file_counts.get("txt", 0) + 1
                    print(f"    [OK] Loaded {len(rows)} chunk(s)")
                    for row in rows:
                        all_rows.append((row, str(p), False))
                except Exception as e:
                    print(f"    [WARN] Could not parse: {e}")

        # --- MD --- (reuses the TXT loader; it already splits by markdown headers)
        if "md" in files_by_type:
            for p in files_by_type["md"]:
                global_idx += 1
                try:
                    print(f"\n[{global_idx}/{total_files}] MD: {p.name}")
                    rows = load_txt_rows(p)
                    file_counts["md"] = file_counts.get("md", 0) + 1
                    print(f"    [OK] Loaded {len(rows)} chunk(s)")
                    for row in rows:
                        all_rows.append((row, str(p), False))
                except Exception as e:
                    print(f"    [WARN] Could not parse: {e}")

        # --- PDF ---
        if "pdf" in files_by_type:
            for p in files_by_type["pdf"]:
                global_idx += 1
                try:
                    print(f"\n[{global_idx}/{total_files}] PDF: {p.name}")
                    rows = load_pdf_rows(p)
                    file_counts["pdf"] = file_counts.get("pdf", 0) + 1
                    print(f"    [OK] Loaded {len(rows)} page(s)")
                    for row in rows:
                        all_rows.append((row, str(p), False))
                except Exception as e:
                    print(f"    [WARN] Could not parse: {e}")

        # --- SQL ---
        if "sql" in files_by_type:
            for p in files_by_type["sql"]:
                global_idx += 1
                try:
                    print(f"\n[{global_idx}/{total_files}] SQL: {p.name}")
                    rows = load_sql_rows(p)
                    file_counts["sql"] = file_counts.get("sql", 0) + 1
                    print(f"    [OK] Loaded {len(rows)} statement(s)")
                    for row in rows:
                        all_rows.append((row, str(p), False))
                except Exception as e:
                    print(f"    [WARN] Could not parse: {e}")

        # --- Excel (xlsx) ---
        for ext in ("xlsx", "xls"):
            if ext in files_by_type:
                for p in files_by_type[ext]:
                    global_idx += 1
                    try:
                        print(f"\n[{global_idx}/{total_files}] EXCEL: {p.name}")
                        rows = load_excel_rows(p)
                        file_counts["excel"] = file_counts.get("excel", 0) + 1
                        print(f"    [OK] Loaded {len(rows)} row(s)")
                        for row in rows:
                            all_rows.append((row, str(p), False))
                    except Exception as e:
                        print(f"    [WARN] Could not parse: {e}")

        total_rows = len(all_rows)
        counts_str = " + ".join(f"{v} {k.upper()}" for k, v in file_counts.items())
        print(f"\n{'='*50}")
        print(f"TOTAL: {total_rows} rows from {counts_str}")
        print(f"{'='*50}")
    else:
        # Single file mode
        suffix = dataset_path.suffix.lower().lstrip(".")
        print(f"\n[FILE] Processing single file: {dataset_path}")

        if suffix == "json":
            rows = load_json_rows(dataset_path)
            use_cases_format = len(rows) > 0 and isinstance(rows[0], dict) and "prompt" in rows[0] and "intent" in rows[0]
            for row in rows:
                all_rows.append((row, str(dataset_path), bool(use_cases_format and isinstance(row, dict) and "prompt" in row)))
            file_counts["json"] = 1
            print(f"    [OK] Loaded {len(rows)} record(s) from JSON")
        elif suffix == "csv":
            df = pd.read_csv(dataset_path, on_bad_lines='warn', engine='python', quotechar='"')
            print(f"    [OK] Loaded {len(df)} rows x {len(df.columns)} columns")
            for _, row in df.iterrows():
                all_rows.append((row.to_dict(), str(dataset_path), False))
            file_counts["csv"] = 1
        elif suffix == "txt":
            rows = load_txt_rows(dataset_path)
            for row in rows:
                all_rows.append((row, str(dataset_path), False))
            file_counts["txt"] = 1
            print(f"    [OK] Loaded {len(rows)} chunk(s) from TXT")
        elif suffix == "pdf":
            rows = load_pdf_rows(dataset_path)
            for row in rows:
                all_rows.append((row, str(dataset_path), False))
            file_counts["pdf"] = 1
            print(f"    [OK] Loaded {len(rows)} page(s) from PDF")
        elif suffix == "sql":
            rows = load_sql_rows(dataset_path)
            for row in rows:
                all_rows.append((row, str(dataset_path), False))
            file_counts["sql"] = 1
            print(f"    [OK] Loaded {len(rows)} statement(s) from SQL")
        elif suffix in ("xlsx", "xls"):
            rows = load_excel_rows(dataset_path)
            for row in rows:
                all_rows.append((row, str(dataset_path), False))
            file_counts["excel"] = 1
            print(f"    [OK] Loaded {len(rows)} row(s) from Excel")
        else:
            raise ValueError(f"Unsupported file format: .{suffix}")

    if not all_rows:
        raise ValueError("No rows to embed (dataset is empty or all files failed to parse)")

    # ==========================================================================
    # STEP 2: CONVERT ROWS TO TEXT
    # ==========================================================================
    print(f"\n[STEP 2] Converting rows to text documents...")
    print("-" * 50)

    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    skipped = 0

    for i, (row_dict, source_path, is_json_use_case) in enumerate(all_rows):
        if is_json_use_case:
            row_for_text = use_case_to_row(row_dict)
            raw_for_meta = row_dict  # full use_case for provision-intent
        else:
            row_for_text = row_dict  # CSV row; row_to_text uses _clean() which handles NaN/None
            raw_for_meta = {str(k): ("" if pd.isna(v) else str(v)) for k, v in row_dict.items()}

        text = row_to_text(row_for_text)
        if not text.strip():
            skipped += 1
            continue

        texts.append(text)
        doc_type = "deployment" if raw_for_meta.get("intent") else None
        meta_entry = {
            "id": i,
            "text": text,
            "source": source_path,
            "raw": raw_for_meta,
        }
        if doc_type:
            meta_entry["type"] = doc_type
        metadatas.append(meta_entry)

        if (i + 1) % 50 == 0:
            print(f"    [OK] Processed {i + 1} rows...")

    print(f"\n    [OK] Converted {len(texts)} rows to text documents")
    if skipped > 0:
        print(f"    [WARN] Skipped {skipped} empty rows")

    # ==========================================================================
    # STEP 3: LOAD EMBEDDING MODEL
    # ==========================================================================
    print(f"\n[STEP 3] Loading embedding model...")
    print("-" * 50)
    print(f"    Model: {args.embedding_model}")

    model = SentenceTransformer(args.embedding_model, trust_remote_code=True)

    # Ensure tokenizer has a pad token (required for batched encode; many causal LMs don't set it)
    if getattr(model.tokenizer, "pad_token", None) is None:
        model.tokenizer.pad_token = model.tokenizer.eos_token

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

    index = build_faiss_index(embeddings)

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
    files_summary = "\n".join(f"    {k.upper():6s} files processed: {v}" for k, v in file_counts.items())
    print(f"""
    Summary:
    -----------------------------------------
{files_summary}
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
