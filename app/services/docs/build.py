"""Build the docs index.   python -m app.services.docs.build [--max-pages 400] [--out PATH]"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .service import DocsService


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Crawl vxcloud.io docs and build the retrieval index.")
    ap.add_argument("--max-pages", type=int, default=400)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--base-url", default="https://vxcloud.io")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    svc = DocsService(args.out)
    res = asyncio.run(svc.reindex(base_url=args.base_url, max_pages=args.max_pages))
    print(res)
    if svc.last_errors:
        print(f"{len(svc.last_errors)} pages failed (first 5): {list(svc.last_errors.items())[:5]}")
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
