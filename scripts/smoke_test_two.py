"""
Smoke-test the two new specialists (CodingLLM, SupportLLM).

Loads each backend directly (no FastAPI) using the cached Qwen 0.5B fallback
(since training ran out of wall-clock), and fires one representative prompt.

Also exercises the universal router's keyword classifier.

Run from repo root:
    TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python3 -m scripts.smoke_test_two
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    os.chdir(repo)

    base = _load("sb", repo / "app/services/ai/ml/specialist_base.py")
    cd = _load("codingllm_backend", repo / "app/services/ai/ml/codingllm/backend.py")
    su = _load("supportllm_backend", repo / "app/services/ai/ml/supportllm/backend.py")

    cases = [
        (
            "codingllm", cd.build_codingllm_config(device="cpu"),
            "Write a Gin handler `DeleteWorkspace` that handles DELETE /api/v2/studio/workspaces/:id. Soft-delete only. Return 204 on success.",
        ),
        (
            "supportllm", su.build_supportllm_config(device="cpu"),
            "How do I deploy the prodxcloud frontend to a VM using the vxcloud deploy script?",
        ),
    ]

    failures = 0
    for slug, cfg, prompt in cases:
        print("\n" + "=" * 72)
        print(f"[{slug}]  {cfg.display_name}")
        print(f"  model_path     = {cfg.model_path}")
        print(f"  dataset_dir    = {cfg.dataset_dir}")
        if cfg.precompute_dir:
            print(f"  precompute_dir = {cfg.precompute_dir}")

        backend = base.SpecialistBackend(cfg)
        t0 = time.time()
        backend.load()
        load_ms = (time.time() - t0) * 1000
        if not backend.loaded:
            print(f"  LOAD FAILED after {load_ms:.0f}ms")
            failures += 1
            continue
        print(f"  loaded_from = {backend.loaded_from}")
        print(f"  device = {backend.effective_device}  load_ms = {load_ms:.0f}")

        t0 = time.time()
        out = backend.generate(prompt, max_new_tokens=120, temperature=0.2)
        gen_ms = (time.time() - t0) * 1000
        resp = str(out.get("response", ""))
        print(f"  gen_ms = {gen_ms:.0f}  response_chars = {len(resp)}")
        print(f"  prompt:   {prompt}")
        print(f"  response: {resp[:480]}")

    # Universal router keyword classifier covers both models' intents
    print("\n" + "=" * 72)
    print("[universal] keyword intent classifier")
    uv = _load("universal", repo / "app/services/ai/ml/universal.py")
    checks = [
        ("Write a Gin handler for POST /api/v2/studio/snippets", "codingllm"),
        ("Refactor this function to use early returns", "codingllm"),
        ("Write a FastAPI endpoint that returns users paginated", "codingllm"),
        ("Review this TypeScript diff for correctness", "codingllm"),
        ("How do I pay with Bitcoin on prodxcloud?", "supportllm"),
        ("I see Invalid studio session in my URL", "supportllm"),
        ("How do I deploy the frontend to S3 and CloudFront?", "cloudllm"),
        ("Destructive edit blocked when saving", "supportllm"),
    ]
    ok = 0
    for p, expected in checks:
        got, scores = uv.classify_intent(p)
        mark = "OK" if got == expected else "--"
        if got == expected:
            ok += 1
        print(f"  [{mark}] {p!r:<60} -> {got}  (expected {expected})")

    print("\n" + "=" * 72)
    print(f"done. classifier {ok}/{len(checks)}. backend failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
