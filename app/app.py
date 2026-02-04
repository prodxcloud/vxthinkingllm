"""
VaLLM - Vector-based Local LLM for Cloud Operations
=====================================================
FastAPI application with embeddings, FAISS, and chain-of-thoughts reasoning.

A sovereign, private AI reasoning engine for cloud infrastructure operations.
Unlike generic LLMs, VaLLM is grounded in your actual production data (logs,
resources, configurations) and provides precise DevOps intelligence.

ARCHITECTURE:
=============
    ┌─────────────────────────────────────────────────────────────┐
    │                      VaLLM CORE                             │
    ├─────────────────────────────────────────────────────────────┤
    │  Embeddings (sentence-transformers/all-MiniLM-L6-v2)        │
    │  Vector Store (FAISS) ─────► Semantic Search                │
    │  LLM Model (distilgpt2/Mistral) ─────► Text Generation      │
    │  Reasoning Engine ─────► Chain-of-Thought Analysis          │
    │  NLP (spaCy) ─────► Entity Extraction (optional)            │
    └─────────────────────────────────────────────────────────────┘

MEMORY & CONTEXT:
=================
    - Session Memory: In-memory conversation history per request
    - Vector Memory: FAISS index for semantic retrieval (long-term)
    - Context Window: Managed by LLM token limits
    - For multi-tenant: Add PostgreSQL for persistent sessions

DATA FLOW:
==========
    1. precompute.py → Embeds CSVs → FAISS index (vectorstore/)
    2. train.py → Fine-tunes LLM on CSVs → Model weights (model/)
    3. app.py → Loads both → Serves API endpoints

USAGE:
======
    # Quick start
    python -m app.app

    # With auto-train enabled
    set VALLM_AUTO_TRAIN=true && python -m app.app  (Windows)
    VALLM_AUTO_TRAIN=true python -m app.app         (Linux/Mac)

ENVIRONMENT VARIABLES:
======================
    VALLM_AUTO_PRECOMPUTE=true  (default: true)  - Auto-build FAISS if missing
    VALLM_AUTO_TRAIN=true       (default: false) - Auto-train LLM if missing
    USE_CUDA=true               (default: false) - Use GPU for inference
    VALLM_CACHE_EMBEDDINGS=true (default: true)  - Cache query embeddings (L1, TTL 1h)
    VALLM_CACHE_SEARCH=true     (default: true)  - Cache search results (L2, TTL 30m)
    VALLM_CACHE_EMBEDDINGS_MAXSIZE (default: 2000)
    VALLM_CACHE_SEARCH_MAXSIZE     (default: 1000)

API ENDPOINTS:
==============
    Core:
        GET  /health              - Health check
        GET  /health/ready        - Readiness probe (enhanced)
        GET  /health/live         - Liveness probe (enhanced)
        GET  /metrics             - Prometheus metrics
        GET  /logs                - View recent logs
        POST /search              - Vector similarity search
        POST /generate            - LLM text generation
    
    V1 (RAG + Reasoning):
        POST /api/model/v1/query     - RAG query with reasoning
        POST /api/model/v1/developer - Developer assistance
        POST /api/model/v1/terminal  - Terminal/CLI assistance
    
    V2 (NLP + Document Analysis):
        POST /api/model/v2/query     - NLP-enhanced query
        POST /api/model/v2/extract   - Entity extraction
        POST /api/model/v2/upload    - Document/image upload
        GET  /api/model/v2/status    - NLP capabilities status
    
    V3 (Cloud/DevOps Incident Patterns):
        POST /api/model/v3/query     - Unusual incident patterns + metrics

DEPLOYMENT:
===========
    Single Node:  python -m app.app
    Production:   uvicorn app.app:app --host 0.0.0.0 --port 8000 --workers 4
    Docker:       docker run -p 8000:8000 vallm:latest
    Kubernetes:   See README.md for deployment manifests
"""

import os
import sys
import json
import logging
import time
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import faiss
import torch
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from starlette.middleware.base import BaseHTTPMiddleware

# =============================================================================
# AUTO-BUILD CONFIGURATION
# =============================================================================
# Set to True to automatically run precompute.py when FAISS index is missing
AUTO_PRECOMPUTE = os.getenv("VALLM_AUTO_PRECOMPUTE", "true").lower() == "true"
# Set to True to automatically run train.py when model is missing (takes longer!)
AUTO_TRAIN = os.getenv("VALLM_AUTO_TRAIN", "false").lower() == "true"

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Create logs directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "logs.txt"

# Custom formatter for beautiful logs
class VaLLMFormatter(logging.Formatter):
    """Custom formatter with colors and structured output"""
    
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        # Add color for console
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Build the log message
        if hasattr(record, 'request_id'):
            prefix = f"[{timestamp}] [{record.levelname:8}] [REQ:{record.request_id[:8]}]"
        else:
            prefix = f"[{timestamp}] [{record.levelname:8}]"
        
        # Add color for terminal output
        if hasattr(record, 'use_color') and record.use_color:
            return f"{color}{prefix}{reset} {record.getMessage()}"
        return f"{prefix} {record.getMessage()}"


# Configure logger
logger = logging.getLogger("vallm")
logger.setLevel(logging.DEBUG)

# Console handler (with colors)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = VaLLMFormatter()
console_handler.setFormatter(console_formatter)

# File handler (no colors, detailed)
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def log_request(request_id: str, method: str, path: str, client: str, body: dict = None):
    """Log incoming request"""
    log_entry = {
        "type": "REQUEST",
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "path": path,
        "client_ip": client,
        "body_preview": str(body)[:200] if body else None
    }
    
    # Console log
    logger.info(f"→ {method} {path} | Client: {client}")
    
    # Detailed file log
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"REQUEST | {datetime.utcnow().isoformat()}\n")
        f.write(f"{'='*80}\n")
        f.write(json.dumps(log_entry, indent=2))
        f.write("\n")


def log_response(request_id: str, status_code: int, duration_ms: float, response_preview: str = None):
    """Log outgoing response"""
    log_entry = {
        "type": "RESPONSE",
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "response_preview": response_preview[:300] if response_preview else None
    }
    
    # Status emoji
    if status_code < 300:
        status_icon = "✓"
    elif status_code < 400:
        status_icon = "→"
    elif status_code < 500:
        status_icon = "⚠"
    else:
        status_icon = "✗"
    
    # Console log
    logger.info(f"← {status_icon} {status_code} | {duration_ms:.2f}ms")
    
    # Detailed file log
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\nRESPONSE | {datetime.utcnow().isoformat()}\n")
        f.write(f"{'-'*40}\n")
        f.write(json.dumps(log_entry, indent=2))
        f.write(f"\n{'='*80}\n\n")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Try to get request body for POST requests
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = json.loads(body_bytes.decode())
                # Reset body for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except:
                pass
        
        # Log request
        log_request(
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            client=client_ip,
            body=body
        )
        
        # Process request and measure time
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            duration_seconds = duration_ms / 1000
            
            # Try to get response body preview
            response_preview = None
            
            # Log response
            log_response(
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_preview=response_preview
            )
            
            # Record Prometheus metrics (if available)
            try:
                try:
                    from .services.ai.ml.metrics import (
                        http_requests_total,
                        http_request_duration_seconds,
                        normalize_path
                    )
                except ImportError:
                    from services.ai.ml.metrics import (
                        http_requests_total,
                        http_request_duration_seconds,
                        normalize_path
                    )
                normalized_path = normalize_path(str(request.url.path))
                http_requests_total.labels(
                    method=request.method,
                    endpoint=normalized_path,
                    status_code=response.status_code
                ).inc()
                http_request_duration_seconds.labels(
                    method=request.method,
                    endpoint=normalized_path
                ).observe(duration_seconds)
            except ImportError:
                pass  # Metrics not available, continue without them
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            duration_seconds = duration_ms / 1000
            
            # Record error metrics (if available)
            try:
                try:
                    from .services.ai.ml.metrics import (
                        http_requests_total,
                        errors_total,
                        normalize_path
                    )
                except ImportError:
                    from services.ai.ml.metrics import (
                        http_requests_total,
                        errors_total,
                        normalize_path
                    )
                normalized_path = normalize_path(str(request.url.path))
                http_requests_total.labels(
                    method=request.method,
                    endpoint=normalized_path,
                    status_code=500
                ).inc()
                errors_total.labels(
                    error_type=type(e).__name__,
                    endpoint=normalized_path
                ).inc()
            except ImportError:
                pass
            
            logger.error(f"✗ Error: {str(e)} | {duration_ms:.2f}ms")
            raise

# Support both direct execution and module execution
try:
    from .services.ai.ml.embeddings import VectorStore
    from .services.ai.ml.reasoning import ReasoningEngine
    from .services.ai.ml.routes import router, router_v2, router_v3
except ImportError as e:
    # Only fall back when running without a package context.
    if "attempted relative import with no known parent package" in str(e):
        from services.ai.ml.embeddings import VectorStore
        from services.ai.ml.reasoning import ReasoningEngine
        from services.ai.ml.routes import router, router_v2, router_v3
    else:
        raise

# Global instances
vector_store = None
reasoning_engine = None
tokenizer = None
model = None
faiss_index = None


def run_precompute():
    """Run precompute.py to build FAISS index"""
    print("\n" + "=" * 70)
    print("🔧 AUTO-PRECOMPUTE: Building FAISS index...")
    print("=" * 70 + "\n")
    
    # Precompute lives under app/services/ai/ml/
    precompute_script = Path(__file__).parent / "services" / "ai" / "ml" / "precompute.py"
    
    if not precompute_script.exists():
        print("    ❌ precompute.py not found!")
        return False
    
    try:
        # Run precompute as module so package imports work
        result = subprocess.run(
            [sys.executable, "-m", "app.services.ai.ml.precompute"],
            cwd=str(Path(__file__).parent.parent),  # Run from project root
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n    ✅ FAISS index built successfully!")
            return True
        else:
            print(f"\n    ❌ Precompute failed with code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n    ❌ Error running precompute: {e}")
        return False


def run_train():
    """Run train.py to build LLM model"""
    print("\n" + "=" * 70)
    print("🔧 AUTO-TRAIN: Training LLM model (this may take several minutes)...")
    print("=" * 70 + "\n")
    
    # Get the path to train.py
    train_script = Path(__file__).parent / "train.py"
    
    if not train_script.exists():
        print("    ❌ train.py not found!")
        return False
    
    try:
        # Run train.py with 1 epoch for speed
        result = subprocess.run(
            [sys.executable, str(train_script), "--num-train-epochs", "1"],
            cwd=str(Path(__file__).parent.parent),  # Run from project root
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n    ✅ LLM model trained successfully!")
            return True
        else:
            print(f"\n    ❌ Training failed with code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n    ❌ Error running train: {e}")
        return False


def check_csv_files(data_dir: Path) -> int:
    """Check how many CSV files exist in data directory"""
    csv_files = list(data_dir.glob("*.csv"))
    return len(csv_files)


def matrix_print(text: str, style: str = "info"):
    """Matrix-style console output"""
    colors = {
        "header": "\033[92m",  # Green
        "info": "\033[96m",    # Cyan
        "success": "\033[92m", # Green
        "warning": "\033[93m", # Yellow
        "error": "\033[91m",   # Red
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    }
    c = colors.get(style, colors["info"])
    reset = colors["reset"]
    try:
        print(f"{c}{text}{reset}")
    except UnicodeEncodeError:
        # Fallback for Windows consoles that don't support UTF-8
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(f"{c}{safe_text}{reset}")


def display_matrix_banner():
    """Display Matrix-style startup banner (large, wide logo)"""
    # VaLLM logo - original then doubled for 2x width
    raw_lines = [
        "    ██╗   ██╗ █████╗ ██╗     ██╗     ███╗   ███╗",
        "    ██║   ██║██╔══██╗██║     ██║     ████╗ ████║",
        "    ██║   ██║███████║██║     ██║     ██╔████╔██║",
        "    ╚██╗ ██╔╝██╔══██║██║     ██║     ██║╚██╔╝██║",
        "     ╚████╔╝ ██║  ██║███████╗███████╗██║ ╚═╝ ██║",
        "      ╚═══╝  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝",
    ]
    logo_lines = ["  " + "".join(c * 2 for c in line) for line in raw_lines]
    banner = """
\033[92m

"""
    banner += "\n".join(logo_lines)
    banner += """

\033[96m
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                                                                              │
    │          V E C T O R - A U G M E N T E D   L O C A L   L A N G U A G E        │
    │                              M O D E L                                        │
    │                                                                              │
    │           Cloud Operations  •  DevOps Intelligence  •  RAG Engine            │
    │                                                                              │
    └──────────────────────────────────────────────────────────────────────────────┘
\033[0m"""
    try:
        print(banner)
    except UnicodeEncodeError:
        # Simplified banner for consoles with limited character support
        print("\033[92m    VaLLM - Vector-Augmented Local Language Model\033[0m")


def display_loading_bar(text: str, current: int, total: int):
    """Display a loading progress bar"""
    bar_length = 40
    filled = int(bar_length * current / total)
    try:
        bar = "█" * filled + "░" * (bar_length - filled)
        percent = int(100 * current / total)
        print(f"\033[96m    [{bar}] {percent}% - {text}\033[0m")
    except UnicodeEncodeError:
        bar = "#" * filled + "-" * (bar_length - filled)
        percent = int(100 * current / total)
        print(f"\033[96m    [{bar}] {percent}% - {text}\033[0m")


def display_system_info(
    data_dir: Path,
    model_loaded: bool,
    vector_count: int,
    device: str,
    vectorstore_path: Path | None = None,
    model_path: Path | None = None,
):
    """Display system configuration in Matrix style"""
    csv_count = check_csv_files(data_dir)
    vs_path = str(vectorstore_path or data_dir / "vectorstore")[-35:]
    mdl_path = str(model_path or data_dir / "model")[-35:]

    try:
        print("\033[92m")
        print("    ┌─────────────────────────────────────────────────────────┐")
        print("    │                  SYSTEM CONFIGURATION                   │")
        print("    ├─────────────────────────────────────────────────────────┤")
        print(f"    │  📂 Data Directory    : {str(data_dir)[-35:]:<35} │")
        print(f"    │  📦 Vectorstore Path  : {vs_path:<35} │")
        print(f"    │  🤖 Model Path        : {mdl_path:<35} │")
        print(f"    │  📄 CSV Files         : {csv_count:<35} │")
        print(f"    │  🤖 LLM Model         : {'✅ LOADED' if model_loaded else '❌ NOT LOADED':<35} │")
        print(f"    │  📊 Vector Count      : {vector_count:<35} │")
        print(f"    │  💻 Compute Device    : {device.upper():<35} │")
        print(f"    │  🔧 Embedding Model   : all-MiniLM-L6-v2{' '*18} │")
        print(f"    │  📝 Log File          : app/logs/logs.txt{' '*17} │")
        print("    ├─────────────────────────────────────────────────────────┤")
        print("    │                    AUTO-BUILD SETTINGS                  │")
        print("    ├─────────────────────────────────────────────────────────┤")
        print(f"    │  🔄 Auto-Precompute   : {'ON' if AUTO_PRECOMPUTE else 'OFF':<35} │")
        print(f"    │  🔄 Auto-Train        : {'ON' if AUTO_TRAIN else 'OFF':<35} │")
        print("    ├─────────────────────────────────────────────────────────┤")
        print("    │                    API ENDPOINTS                        │")
        print("    ├─────────────────────────────────────────────────────────┤")
        print("    │  GET  /health                      Health check         │")
        print("    │  GET  /logs                        View recent logs     │")
        print("    │  POST /search                      Vector search        │")
        print("    │  POST /generate                    LLM generation       │")
        print("    │  POST /api/model/v1/query          RAG + Reasoning      │")
        print("    │  POST /api/model/v2/query          NLP + Documents      │")
        print("    │  POST /api/model/v3/query          Incident Patterns    │")
        print("    └─────────────────────────────────────────────────────────┘")
        print("\033[0m")
    except UnicodeEncodeError:
        print("\033[92m")
        print("    --- SYSTEM CONFIGURATION ---")
        print(f"    Data Directory    : {str(data_dir)[-35:]}")
        print(f"    Vectorstore Path  : {vs_path}")
        print(f"    Model Path        : {mdl_path}")
        print(f"    CSV Files         : {csv_count}")
        print(f"    LLM Model         : {'LOADED' if model_loaded else 'NOT LOADED'}")
        print(f"    Vector Count      : {vector_count}")
        print(f"    Compute Device    : {device.upper()}")
        print("\033[0m")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global vector_store, reasoning_engine, tokenizer, model, faiss_index
    
    display_matrix_banner()
    
    matrix_print("\n    ⚡ INITIALIZING NEURAL NETWORK SYSTEMS...\n", "header")
    
    try:
        # Step 1: Data Directory
        display_loading_bar("Scanning data directory", 1, 6)
        data_dir = Path(__file__).parent / "data"
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            matrix_print("    ⚠️  Data directory created. Add CSV files to app/data/", "warning")
        
        # Step 2: Vector Store
        display_loading_bar("Loading vector store", 2, 6)
        vector_store = VectorStore(data_dir=str(data_dir))
        await vector_store.initialize()
        matrix_print("    ✓ Vector store initialized", "success")
        
        # Step 3: Reasoning Engine
        display_loading_bar("Initializing reasoning engine", 3, 6)
        reasoning_engine = ReasoningEngine(vector_store)
        await reasoning_engine.initialize()
        matrix_print("    ✓ Reasoning engine online", "success")
        
        # Step 4: LLM Model
        display_loading_bar("Loading LLM model", 4, 6)
        model_dir = data_dir / "model"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if model_dir.exists() and (model_dir / "config.json").exists():
            try:
                tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                model = AutoModelForCausalLM.from_pretrained(str(model_dir)).to(device)
                matrix_print(f"    ✓ LLM model loaded → {device.upper()}", "success")
            except Exception as e:
                matrix_print(f"    ⚠️  LLM model error: {e}", "warning")
                tokenizer = None
                model = None
        else:
            # Check if we should auto-train
            if AUTO_TRAIN:
                csv_count = check_csv_files(data_dir)
                if csv_count > 0:
                    matrix_print(f"    🔄 No LLM model found. Auto-training with {csv_count} CSV files...", "warning")
                    if run_train():
                        # Reload model after training
                        try:
                            tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                            model = AutoModelForCausalLM.from_pretrained(str(model_dir)).to(device)
                            matrix_print(f"    ✓ LLM model trained and loaded → {device.upper()}", "success")
                        except Exception as e:
                            matrix_print(f"    ⚠️  Error loading trained model: {e}", "warning")
                else:
                    matrix_print("    ⚠️  No CSV files found. Add data to app/data/ first.", "warning")
            else:
                matrix_print("    ⚠️  No LLM model found.", "warning")
                matrix_print("    📝 To train: python ./app/services/ai/ml/train.py", "info")
                matrix_print("    💡 Or set VALLM_AUTO_TRAIN=true to auto-train on startup", "info")
        
        # Step 5: FAISS Index
        display_loading_bar("Loading FAISS vector index", 5, 6)
        vectorstore_dir = data_dir / "vectorstore"
        faiss_index_path = vectorstore_dir / "faiss_index.bin"
        vector_count = 0
        
        if faiss_index_path.exists():
            try:
                faiss_index = faiss.read_index(str(faiss_index_path))
                vector_count = faiss_index.ntotal
                matrix_print(f"    ✓ FAISS index loaded → {vector_count} vectors", "success")
            except Exception as e:
                matrix_print(f"    ⚠️  FAISS error: {e}", "warning")
                faiss_index = None
        else:
            # Check if we should auto-precompute
            if AUTO_PRECOMPUTE:
                csv_count = check_csv_files(data_dir)
                if csv_count > 0:
                    matrix_print(f"    🔄 No FAISS index found. Auto-building with {csv_count} CSV files...", "warning")
                    if run_precompute():
                        # Reload FAISS after building
                        try:
                            faiss_index = faiss.read_index(str(faiss_index_path))
                            vector_count = faiss_index.ntotal
                            matrix_print(f"    ✓ FAISS index built and loaded → {vector_count} vectors", "success")
                        except Exception as e:
                            matrix_print(f"    ⚠️  Error loading built index: {e}", "warning")
                else:
                    matrix_print("    ⚠️  No CSV files found. Add data to app/data/ first.", "warning")
            else:
                matrix_print("    ⚠️  No FAISS index found.", "warning")
                matrix_print("    📝 To build: python -m app.services.ai.ml.precompute", "info")
                matrix_print("    💡 Or set VALLM_AUTO_PRECOMPUTE=true (default) to auto-build", "info")
        
        # Step 6: Final Setup
        display_loading_bar("Completing initialization", 6, 7)
        
        # Store in app state
        app.state.vector_store = vector_store
        app.state.reasoning_engine = reasoning_engine
        app.state.tokenizer = tokenizer
        app.state.model = model
        app.state.faiss_index = faiss_index
        
        # Display system info
        display_system_info(
            data_dir=data_dir,
            model_loaded=(model is not None),
            vector_count=vector_count,
            device=device,
            vectorstore_path=vectorstore_dir,
            model_path=model_dir,
        )
        
        matrix_print("    ⚡ VALLM NEURAL NETWORK ONLINE ⚡\n", "header")
        
    except Exception as e:
        matrix_print(f"\n    ❌ CRITICAL ERROR: {e}", "error")
        import traceback
        traceback.print_exc()
        raise
    
    # Step 7: Platform Infrastructure
    display_loading_bar("Initializing platform infrastructure", 6, 7)
    try:
        # Initialize database
        try:
            from .services.platform.database import init_db
        except ImportError:
            from services.platform.database import init_db
        try:
            init_db()
            matrix_print("    ✓ Database initialized", "success")
        except Exception as e:
            matrix_print(f"    ⚠️  Database init warning: {e}", "warning")
            logger.warning(f"Database initialization warning: {e}")

        # Start lifecycle tasks
        try:
            from .services.platform.lifecycle_hooks import start_lifecycle_tasks
        except ImportError:
            from services.platform.lifecycle_hooks import start_lifecycle_tasks
        await start_lifecycle_tasks(app.state)
        matrix_print("    ✓ Lifecycle tasks started", "success")
    except Exception as e:
        matrix_print(f"    ⚠️  Platform infrastructure warning: {e}", "warning")
        logger.warning(f"Platform infrastructure warning: {e}")
    
    yield
    
    # Cleanup
    matrix_print("\n    🔌 SHUTTING DOWN NEURAL SYSTEMS...", "warning")
    if vector_store:
        await vector_store.cleanup()
    if reasoning_engine:
        await reasoning_engine.cleanup()
    
    # Stop lifecycle tasks
    try:
        try:
            from .services.platform.lifecycle_hooks import stop_lifecycle_tasks
        except ImportError:
            from services.platform.lifecycle_hooks import stop_lifecycle_tasks
        await stop_lifecycle_tasks()
    except Exception as e:
        logger.warning(f"Error stopping lifecycle tasks: {e}")
    
    matrix_print("    ✓ Shutdown complete\n", "success")


# Create FastAPI app
app = FastAPI(
    title="VaLLM - Vector-based Local LLM",
    description="Private cloud operations AI with embeddings and chain-of-thoughts reasoning",
    version="1.0.0",
    lifespan=lifespan
)

# Request/Response logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Optional: Legacy rate limiting middleware (if enabled)
try:
    try:
        from .services.ai.ml.rate_limit import RateLimitMiddleware, RATE_LIMIT_ENABLED
    except ImportError:
        from services.ai.ml.rate_limit import RateLimitMiddleware, RATE_LIMIT_ENABLED
    if RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
        logger.info("✅ Legacy rate limiting enabled")
except ImportError:
    pass

# Tenant-aware rate limiting middleware (Redis-based, TPM)
try:
    try:
        from .services.platform.tenant_rate_limit import TenantRateLimitMiddleware, RATE_LIMIT_ENABLED
    except ImportError:
        from services.platform.tenant_rate_limit import TenantRateLimitMiddleware, RATE_LIMIT_ENABLED
    if RATE_LIMIT_ENABLED:
        app.add_middleware(TenantRateLimitMiddleware)
        logger.info("✅ Tenant-aware rate limiting enabled (Redis TPM)")
except ImportError:
    pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Setup JSON logging (if enabled)
try:
    try:
        from .services.ai.ml.logging_config import setup_json_logging
    except ImportError:
        from services.ai.ml.logging_config import setup_json_logging
    setup_json_logging()
except ImportError:
    pass

# Log startup message
logger.info(f"📁 Logs will be saved to: {LOG_FILE}")

# Include routes
app.include_router(router, prefix="/api/model/v1")
app.include_router(router_v2, prefix="/api/model/v2")
app.include_router(router_v3, prefix="/api/model/v3")

# Include platform routes
try:
    try:
        from .services.platform.model_router import router as platform_model_router
        from .services.platform.eval_router import router as platform_eval_router
        from .services.platform.health_probe_router import router as platform_health_router
    except ImportError as e:
        if "attempted relative import with no known parent package" in str(e):
            from services.platform.model_router import router as platform_model_router
            from services.platform.eval_router import router as platform_eval_router
            from services.platform.health_probe_router import router as platform_health_router
        else:
            raise

    app.include_router(platform_model_router)
    app.include_router(platform_eval_router)
    app.include_router(platform_health_router)
    logger.info("✅ Platform routes registered")
except ImportError as e:
    logger.warning(f"Platform routes not available: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Display a beautiful status page for the VaLLM service."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaLLM Status</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: linear-gradient(135deg, #2b5876, #4e4376);
            color: white;
            text-align: center;
        }
        .container {
            padding: 40px;
            border-radius: 15px;
            background: rgba(0, 0, 0, 0.2);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        h1 {
            font-size: 4rem;
            margin-bottom: 10px;
            font-weight: 600;
        }
        p {
            font-size: 1.5rem;
            margin: 5px 0;
        }
        .status {
            display: inline-block;
            padding: 10px 25px;
            border-radius: 25px;
            background-color: #27ae60;
            font-size: 1.5rem;
            font-weight: bold;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>VaLLM</h1>
        <p>Vector-Augmented Local Language Model</p>
        <div class="status">Online</div>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/health")
async def health():
    """Basic health check (for load balancers) - unchanged"""
    return {"status": "healthy"}


# Optional: Enhanced health checks
try:
    try:
        from .services.ai.ml.health import HealthChecker
    except ImportError:
        from services.ai.ml.health import HealthChecker

    @app.get("/health/ready")
    async def readiness():
        """Readiness probe - checks if service can accept traffic"""
        checker = HealthChecker(app.state)
        health_data = await checker.check_health()

        if health_data["status"] != "healthy":
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=health_data)

        return health_data

    @app.get("/health/live")
    async def liveness():
        """Liveness probe - checks if service is alive"""
        return {"status": "alive"}
except ImportError:
    pass


# Prometheus metrics endpoint
# Access at: http://localhost:8000/metrics
try:
    try:
        from .services.ai.ml.metrics import get_metrics_response
    except ImportError:
        from services.ai.ml.metrics import get_metrics_response

    @app.get("/metrics")
    async def metrics():
        """
        Prometheus metrics endpoint

        Returns metrics in Prometheus format for scraping.
        Access at: http://localhost:8000/metrics
        """
        return get_metrics_response()
except ImportError:
    # Metrics not available if prometheus-client not installed
    logger.warning("Prometheus metrics not available (prometheus-client not installed)")
    pass


@app.get("/logs")
async def get_logs(lines: int = 50):
    """
    View recent logs
    
    Args:
        lines: Number of recent lines to return (default 50)
    """
    try:
        if not LOG_FILE.exists():
            return {"logs": [], "message": "No logs yet"}
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "log_file": str(LOG_FILE),
            "total_lines": len(all_lines),
            "showing": len(recent_lines),
            "logs": [line.rstrip() for line in recent_lines]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/logs/stats")
async def get_log_stats():
    """Get logging statistics"""
    try:
        if not LOG_FILE.exists():
            return {"message": "No logs yet"}
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count requests and responses
        request_count = content.count('"type": "REQUEST"')
        response_count = content.count('"type": "RESPONSE"')
        error_count = content.count('ERROR')
        
        # Get file size
        file_size = LOG_FILE.stat().st_size
        
        return {
            "log_file": str(LOG_FILE),
            "file_size_kb": round(file_size / 1024, 2),
            "total_requests": request_count,
            "total_responses": response_count,
            "errors": error_count,
            "created": datetime.fromtimestamp(LOG_FILE.stat().st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(LOG_FILE.stat().st_mtime).isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@app.delete("/logs/clear")
async def clear_logs():
    """Clear all logs"""
    try:
        if LOG_FILE.exists():
            # Backup before clearing
            backup_file = LOG_DIR / f"logs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            LOG_FILE.rename(backup_file)
            
            # Create new empty log file
            LOG_FILE.touch()
            
            logger.info("🗑️ Logs cleared (backup created)")
            
            return {
                "message": "Logs cleared",
                "backup": str(backup_file)
            }
        return {"message": "No logs to clear"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/stats")
async def get_stats(request: Request):
    """
    Vector store and cache statistics.
    Includes total_vectors, by_type, and cache (embedding L1, search L2) stats when enabled.
    """
    try:
        vs = getattr(request.app.state, "vector_store", None)
        if vs is None:
            return {"error": "Vector store not initialized"}
        return await vs.get_vector_store_stats()
    except Exception as e:
        return {"error": str(e)}


class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 200
    temperature: float = 0.7
    top_p: float = 0.9


class GenerateResponse(BaseModel):
    response: str
    text: str  # Alias for LangChain compatibility
    model_loaded: bool
    device: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    text: str
    score: float
    metadata: dict


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text using the trained LLM model"""
    global tokenizer, model
    
    if tokenizer is None or model is None:
        fallback_msg = "Model not loaded. Please run 'python ./app/train.py' first to train and export the model."
        logger.warning("LLM input/output skipped (model not loaded)")
        return GenerateResponse(
            response=fallback_msg,
            text=fallback_msg,
            model_loaded=False,
            device="none"
        )
    
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"LLM input: {request.prompt}")
        inputs = tokenizer(request.prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        logger.info(f"LLM output: {generated_text}")
        
        return GenerateResponse(
            response=generated_text,
            text=generated_text,  # For LangChain compatibility
            model_loaded=True,
            device=device
        )
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        return GenerateResponse(
            response=error_msg,
            text=error_msg,
            model_loaded=True,
            device="error"
        )


@app.post("/search")
async def search(request: SearchRequest):
    """
    Search the vector store for relevant documents.
    This endpoint is compatible with LangChain retrievers.
    
    Returns:
        {"results": [{"text": "...", "score": 0.12, "metadata": {...}}, ...]}
    """
    global vector_store
    
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    try:
        search_results = await vector_store.search(
            query=request.query,
            top_k=request.top_k
        )
        
        # Format for LangChain compatibility
        results = []
        for r in search_results:
            results.append({
                "text": r.get("document", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {})
            })
        
        return {"results": results}
    
    except Exception as e:
        import traceback
        logger.error(f"Search error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search error: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # Ensure root directory is in sys.path for uvicorn imports
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    # Handle Windows encoding issues for special characters
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, Exception):
            pass

    uvicorn.run(
        app,  # Pass the app object directly to avoid double import issues
        host="0.0.0.0",
        port=8002,
        reload=False
    )

