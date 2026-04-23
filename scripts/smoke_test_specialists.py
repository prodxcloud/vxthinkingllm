"""Smoke-test CloudLLM / CodingLLM / SupportLLM + universal keyword router.

Loads each SpecialistBackend directly (no FastAPI, no auto-train) and
fires one representative prompt at each. Prints a compact report:

    [cloudllm]  loaded_from=.../models/cloudllm  device=cpu  chars=NNN
    prompt: ...
    response: ...

Run from repo root:
    TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python3 -m scripts.smoke_test_specialists
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

    # Load specialist_base directly — avoids triggering app.services.ai.ml/__init__
    # which pulls sentence_transformers (broken under transformers 5.x here).
    base = _load("sb", repo / "app/services/ai/ml/specialist_base.py")
    cl = _load("cloudllm_backend", repo / "app/services/ai/ml/cloudllm/backend.py")
    cd = _load("codingllm_backend", repo / "app/services/ai/ml/codingllm/backend.py")
    su = _load("supportllm_backend", repo / "app/services/ai/ml/supportllm/backend.py")

    models = [
        (
            "cloudllm", cl.build_cloudllm_config(device="cpu"),
            "Write a Kubernetes Deployment manifest for a FastAPI service with 3 replicas and resource limits.",
        ),
        (
            "codingllm", cd.build_codingllm_config(device="cpu"),
            "Write a Python function flatten(d) that flattens a nested dict using dot-notation keys.",
        ),
        (
            "supportllm", su.build_supportllm_config(device="cpu"),
            "How do I deploy the prodxcloud frontend to a VM using the valtunox deploy script?",
        ),
    ]

    failures = 0
    for slug, cfg, prompt in models:
        print("\n" + "=" * 72)
        print(f"[{slug}]  {cfg.display_name}")
        print(f"  paths: model_path={cfg.model_path}  dataset_dir={cfg.dataset_dir}")
        backend = base.SpecialistBackend(cfg)
        t0 = time.time()
        backend.load()
        load_ms = (time.time() - t0) * 1000
        if not backend.loaded:
            print(f"  LOAD FAILED after {load_ms:.0f}ms")
            failures += 1
            continue
        print(f"  loaded_from={backend.loaded_from}  device={backend.effective_device}  load_ms={load_ms:.0f}")

        t0 = time.time()
        out = backend.generate(prompt, max_new_tokens=120, temperature=0.3)
        gen_ms = (time.time() - t0) * 1000
        response = str(out.get("response", ""))[:400]
        print(f"  gen_ms={gen_ms:.0f}  response_chars={len(out.get('response',''))}")
        print(f"  prompt:   {prompt}")
        print(f"  response: {response}")

    # Universal keyword router
    print("\n" + "=" * 72)
    print("[universal] keyword intent classifier")
    # load the universal module too (pure stdlib, no torch imports)
    uv = _load("universal", repo / "app/services/ai/ml/universal.py")
    for p, expect in [
        ("Terraform module for VPC with KMS-encrypted flow logs", "cloudllm"),
        ("Refactor this function to use early returns", "codingllm"),
        ("How do I reset my MFA device?", "supportllm"),
        ("Estimate story points for this sprint backlog", "thinkingllm"),
        ("random chit chat", "supportllm"),
    ]:
        got, scores = uv.classify_intent(p)
        mark = "OK" if got == expect else "--"
        print(f"  [{mark}] {p!r:<55} -> {got}  (expected {expect})")

    print("\n" + ("=" * 72))
    print(f"done. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
