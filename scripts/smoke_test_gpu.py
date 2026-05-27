"""Fast GPU smoke test for the 3 specialist models.

Loads each SpecialistBackend directly on CUDA, generates a short response
(40 tokens), and prints a one-line per-model summary plus the response.
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
    cl = _load("cloudllm_backend", repo / "app/services/ai/ml/cloudllm/backend.py")
    cd = _load("codingllm_backend", repo / "app/services/ai/ml/codingllm/backend.py")
    su = _load("supportllm_backend", repo / "app/services/ai/ml/supportllm/backend.py")

    models = [
        ("cloudllm", cl.build_cloudllm_config(device="cuda"),
         "Write a Kubernetes Deployment manifest for a FastAPI service with 3 replicas and resource limits."),
        ("codingllm", cd.build_codingllm_config(device="cuda"),
         "Write a Python function flatten(d) that flattens a nested dict using dot-notation keys."),
        ("supportllm", su.build_supportllm_config(device="cuda"),
         "How do I deploy the prodxcloud frontend to a VM using the vxcloud deploy script?"),
    ]

    failures = 0
    for slug, cfg, prompt in models:
        print("=" * 72)
        print(f"[{slug}] {cfg.display_name}")
        print(f"  model_path = {cfg.model_path}")
        backend = base.SpecialistBackend(cfg)
        t0 = time.time()
        backend.load()
        load_ms = (time.time() - t0) * 1000
        if not backend.loaded:
            print(f"  LOAD FAILED after {load_ms:.0f}ms")
            failures += 1
            continue
        print(f"  loaded_from = {backend.loaded_from}")
        print(f"  device      = {backend.effective_device}   load_ms = {load_ms:.0f}")

        t0 = time.time()
        out = backend.generate(prompt, max_new_tokens=40, temperature=0.3)
        gen_ms = (time.time() - t0) * 1000
        response = str(out.get("response", "")).strip()
        print(f"  gen_ms      = {gen_ms:.0f}   chars = {len(response)}")
        print(f"  prompt   : {prompt}")
        print(f"  response : {response[:600]}")

        # Free VRAM between models
        try:
            import torch
            del backend
            torch.cuda.empty_cache()
        except Exception:
            pass
        print()

    print("=" * 72)
    print(f"done. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
