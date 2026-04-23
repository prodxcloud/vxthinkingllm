"""
CodingLLM precompute — AST index of the repository.

Scans the repo and builds a lightweight AST index (symbols, imports, file map)
written to `app/data/precompute/codingllm/index.json`. This is consumed at
inference time to ground generations in the actual codebase.

Falls back to a Python-only `ast`-based indexer when `tree_sitter_languages`
isn't installed, so the script always runs on a clean environment.

QUICK START (from repo root):
    python -m app.services.ai.ml.codingllm.precompute.index_codebase
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tree_sitter_languages import get_parser  # type: ignore
    HAVE_TREE_SITTER = True
except Exception:  # pragma: no cover
    HAVE_TREE_SITTER = False


DEFAULT_OUT = Path("app") / "data" / "precompute" / "codingllm" / "index.json"
SKIP_DIR_NAMES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", ".next", ".cache",
    "_checkpoints", "models", "vectorstore",
}
# File types we actually index (extend as needed)
CODE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}


@dataclass
class FileIndex:
    path: str
    language: str
    imports: List[str] = field(default_factory=list)
    symbols: List[Dict[str, str]] = field(default_factory=list)  # {kind, name, line}
    size_bytes: int = 0


def _lang_for(ext: str) -> str:
    return {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
    }.get(ext, "text")


def _index_python(src: str, rel_path: str) -> FileIndex:
    idx = FileIndex(path=rel_path, language="python", size_bytes=len(src.encode("utf-8")))
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return idx

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                idx.imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for n in node.names:
                idx.imports.append(f"{mod}.{n.name}" if mod else n.name)
        elif isinstance(node, ast.ClassDef):
            idx.symbols.append({"kind": "class", "name": node.name, "line": str(node.lineno)})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            idx.symbols.append({"kind": "function", "name": node.name, "line": str(node.lineno)})
    return idx


def _index_tree_sitter(src: str, rel_path: str, language: str) -> FileIndex:
    """Tree-sitter path (TS/JS/Go/Rust). Gracefully degrades to an empty index
    if parsing fails or the language pack isn't available."""
    idx = FileIndex(path=rel_path, language=language, size_bytes=len(src.encode("utf-8")))
    if not HAVE_TREE_SITTER:
        return idx
    try:
        parser = get_parser(language)
        tree = parser.parse(src.encode("utf-8"))
        root = tree.root_node

        def walk(node):
            if node.type in {"function_declaration", "method_definition", "function_definition"}:
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    idx.symbols.append({
                        "kind": "function",
                        "name": src[name_node.start_byte:name_node.end_byte],
                        "line": str(node.start_point[0] + 1),
                    })
            elif node.type in {"class_declaration", "class_definition"}:
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    idx.symbols.append({
                        "kind": "class",
                        "name": src[name_node.start_byte:name_node.end_byte],
                        "line": str(node.start_point[0] + 1),
                    })
            elif node.type in {"import_statement", "import_declaration"}:
                idx.imports.append(src[node.start_byte:node.end_byte].strip())
            for child in node.children:
                walk(child)

        walk(root)
    except Exception:
        pass
    return idx


def index_repo(root: Path, max_file_bytes: int = 500_000) -> Dict:
    files: List[FileIndex] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in CODE_EXTS:
                continue
            fpath = Path(dirpath) / fname
            try:
                if fpath.stat().st_size > max_file_bytes:
                    continue
                src = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(fpath.relative_to(root))
            language = _lang_for(ext)
            if language == "python":
                files.append(_index_python(src, rel))
            else:
                files.append(_index_tree_sitter(src, rel, language))

    return {
        "root": str(root),
        "file_count": len(files),
        "symbol_count": sum(len(f.symbols) for f in files),
        "languages": sorted({f.language for f in files}),
        "uses_tree_sitter": HAVE_TREE_SITTER,
        "files": [asdict(f) for f in files],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CodingLLM AST index")
    parser.add_argument("--root", type=str, default=".", help="Repo root to index")
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"[CodingLLM precompute] indexing {root} (tree-sitter: {HAVE_TREE_SITTER})")
    index = index_repo(root)
    with out.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(
        f"[CodingLLM precompute] wrote {out} "
        f"(files={index['file_count']}, symbols={index['symbol_count']})"
    )


if __name__ == "__main__":
    main()
