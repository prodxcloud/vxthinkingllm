"""
CodingLLMBackend — VxCoder v1.0
================================
Code generation / multi-file edit / PR review / test writing specialist.

Mirrors the VxThinkingLLM load + generate pattern via SpecialistBackend.
"""

from __future__ import annotations

try:
    from ..specialist_base import (
        SpecialistBackend,
        SpecialistConfig,
        resolve_model_path,
        resolve_dataset_dir,
    )
except ImportError:
    from app.services.ai.ml.specialist_base import (
        SpecialistBackend,
        SpecialistConfig,
        resolve_model_path,
        resolve_dataset_dir,
    )


CODINGLLM_SYSTEM_PROMPT = (
    "You are VxCoder, an expert software engineer on the ProdxCloud stack "
    "(FastAPI, React, TypeScript, Kubernetes).\n\n"
    "Hard rules:\n"
    "1. For edits to existing code, return XML search/replace diffs:\n"
    "   <<<<<<< SEARCH\n   <old lines>\n   =======\n   <new lines>\n   >>>>>>> REPLACE\n"
    "2. For whole-file generation, return a single fenced code block with the "
    "   correct language tag.\n"
    "3. Always write tests alongside features (pytest for Python, vitest for TS).\n"
    "4. Never invent imports — if you reference a symbol, ensure the import is visible.\n"
    "5. Keep each function under 40 lines unless the task genuinely requires more."
)


def build_codingllm_config(device: str = "cuda") -> SpecialistConfig:
    return SpecialistConfig(
        slug="codingllm",
        display_name="VxCoder v1.0",
        model_path=resolve_model_path(
            "CODINGLLM_MODEL_PATH",
            "app/data/models/codingllm",
        ),
        dataset_dir=resolve_dataset_dir(
            "CODINGLLM_DATASET_DIR",
            "app/data/datasets/codingllm",
        ),
        precompute_dir=resolve_dataset_dir(
            "CODINGLLM_PRECOMPUTE_DIR",
            "app/data/precompute/codingllm",
        ),
        fallback_base_model="Qwen/Qwen2.5-0.5B-Instruct",
        system_prompt=CODINGLLM_SYSTEM_PROMPT,
        device=device,
        prefix="/v1/coding",
    )


class CodingLLMBackend(SpecialistBackend):
    pass
