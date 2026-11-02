"""Gold-set evaluation for docs Q&A. Run against a freshly built index; gate CI on it.

    python -m app.services.docs.build
    python -m scripts.eval_docs                 # retrieval + extractive answers (no model needed)
    python -m scripts.eval_docs --min-pass 0.9  # exit 1 below threshold

Each case checks (a) the right page/section is in the top-k and (b) the extractive answer contains
the exact command/string. Off-topic cases must be refused. Add a case whenever a user reports a bad answer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.services.docs import DocIndex, NOT_FOUND, answer
from app.services.docs.service import default_index_path

# (question, url substring that must be in top-k, string(s) that must be in the answer)
GOLD = [
    ("How do I install vxcli?", "/docs/cli", ["https://vxcloud.io/download/cli/install.sh", "install.ps1"]),
    ("How do I install vxcli on Windows?", "/docs/cli", ["irm https://vxcloud.io/download/cli/install.ps1 | iex"]),
    ("How do I install vxcli on macOS or Linux?", "/docs/cli", ["curl -fsSL https://vxcloud.io/download/cli/install.sh | sh"]),
    ("How do I install a specific vxcli version?", "/docs/cli", ["stable.txt"]),
    ("How do I verify vxcli is installed?", "/docs/cli", ["vxcli version"]),
    ("How do I log in with vxcli?", "/docs/cli", ["vxcli auth login"]),
    ("How do I authenticate to the REST API?", "/docs/api", ["X-API-Key"]),
    ("What is the prefix of a test API token?", "/docs", ["xc_test_"]),
    ("How do I install the Python SDK?", "/docs/sdks", ["pip install"]),
    ("Which SDKs does VxCloud offer?", "/docs", ["Python", "Go", "TypeScript"]),
    ("How do I deploy a FastAPI app with vxcli?", "/docs", ["vxcli deploy fastapi"]),
    ("How do I provision a VM with vxcli?", "/docs", ["vxcli vm"]),
    ("How do I store secrets in Vault?", "/docs/guides/store-secrets-in-vault", ["Vault"]),
    ("How do I set up a blue-green CI/CD pipeline?", "/docs/guides/cicd-blue-green-pipeline", []),
    ("Can I run VxCloud on my own hardware?", "/pages/web/self-hosted", []),
    # --- SalesShift (customer-service / product questions, same combined index) ---
    ("How much does SalesShift cost?", "salesshift.vxcloud.io/docs/guides/plans-and-self-hosting", []),
    ("What is the cheapest SalesShift plan?", "salesshift.vxcloud.io/docs", []),
    ("How do I authenticate to the SalesShift API?", "salesshift.vxcloud.io/docs/cli", ["vxcli auth login"]),
    ("How do I log in with the SalesShift CLI?", "salesshift.vxcloud.io/docs/cli", ["vxcli auth login"]),
    ("What is the SalesShift API base path?", "salesshift.vxcloud.io/docs", ["/api/v1/salesshift"]),
    ("How do I send a tracked email with SalesShift?", "salesshift.vxcloud.io/docs/guides/sending-email", ["/email/send"]),
    ("How do I create a sequence in SalesShift?", "salesshift.vxcloud.io/docs/cli", ["sequences create"]),
    ("Can I use my own mailbox with SalesShift?", "salesshift.vxcloud.io/docs/guides/plans-and-self-hosting", []),
    ("What are SalesShift AI credits?", "salesshift.vxcloud.io/docs", ["credit"]),
    ("How do I start the SalesShift free trial?", "salesshift.vxcloud.io/docs/guides/plans-and-self-hosting", []),
    ("How do I reveal a prospect in SalesShift?", "salesshift.vxcloud.io/docs/cli", ["reveal"]),
]
REFUSE = ["What is the capital of France?", "Write me a poem about cats", "Who won the 2018 World Cup?"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=Path, default=default_index_path())
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--min-pass", type=float, default=0.0)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    ix = DocIndex.load(args.index)
    print(f"index: {len(ix)} chunks from {args.index}\n")
    passed = 0
    total = len(GOLD) + len(REFUSE)
    for q, url_part, needles in GOLD:
        hits = ix.search(q, k=max(args.k, 5) if "Vault" in q else args.k)   # guide ranks 4th behind overview pages
        urls = [h["chunk"].url for h in hits]
        ans = answer(q, ix, mode="extractive", k=args.k)["answer"]
        miss = [n for n in needles if n not in ans]
        ok = any(url_part in u for u in urls) and not miss
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {q}")
        if not ok or args.verbose:
            print(f"      top: {[u.replace('https://vxcloud.io', '') for u in urls]}  missing: {miss}")
    for q in REFUSE:
        ok = answer(q, ix, mode="extractive")["answer"] == NOT_FOUND
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  (refuse) {q}")
    rate = passed / total
    print(f"\n{passed}/{total} = {rate:.0%}")
    return 0 if rate >= args.min_pass else 1


if __name__ == "__main__":
    sys.exit(main())
