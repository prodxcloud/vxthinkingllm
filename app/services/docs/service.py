"""Process-wide docs service: owns the index, its on-disk location and (re)indexing."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .crawler import crawl
from .index import DocIndex

logger = logging.getLogger("vxthinking.docs.service")


def default_index_path() -> Path:
    raw = os.getenv("VXDOCS_INDEX_PATH")
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[3] / "data" / "docs_index" / "index.json"


class DocsService:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else default_index_path()
        self.index: DocIndex = DocIndex()
        self.built_at: Optional[float] = None
        self.last_errors: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self.reindexing = False

    @property
    def ready(self) -> bool:
        return len(self.index) > 0

    def load(self) -> bool:
        if not self.path.exists():
            return False
        try:
            self.index = DocIndex.load(self.path)
            self.built_at = self.path.stat().st_mtime
            logger.info("docs index loaded: %d chunks from %s", len(self.index), self.path)
            return True
        except Exception as e:
            logger.warning("could not load docs index %s: %s", self.path, e)
            return False

    async def reindex(self, **crawl_kwargs: Any) -> Dict[str, Any]:
        """Crawl -> build -> atomically persist -> swap. Serves the old index until the new one is ready."""
        if self._lock.locked():
            return {"status": "already_running"}
        async with self._lock:
            self.reindexing = True
            t0 = time.perf_counter()
            try:
                chunks, errors = await crawl(**crawl_kwargs)
                if not chunks:
                    return {"status": "failed", "error": "crawl produced no chunks", "errors": errors}
                new = DocIndex(chunks)
                await asyncio.to_thread(new.save, self.path)
                self.index, self.built_at, self.last_errors = new, time.time(), errors
                return {"status": "ok", "chunks": len(new), "pages_with_errors": len(errors),
                        "duration_s": round(time.perf_counter() - t0, 1)}
            finally:
                self.reindexing = False

    def stats(self) -> Dict[str, Any]:
        pages = {c.url for c in self.index.chunks}
        return {"ready": self.ready, "chunks": len(self.index), "pages": len(pages),
                "built_at": self.built_at, "reindexing": self.reindexing, "path": str(self.path)}
