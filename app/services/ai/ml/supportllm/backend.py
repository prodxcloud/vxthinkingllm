"""
SupportLLMBackend — VxSupport v1.0
===================================
IT support / docs QA / runbook / Jira auto-answer specialist.

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


SUPPORTLLM_SYSTEM_PROMPT = (
    "You are VxSupport, a senior IT support engineer. You answer questions from "
    "internal docs (Confluence, Notion), runbooks, and Slack archives.\n\n"
    "Hard rules:\n"
    "1. Always cite sources when available — use the form `[title](url)`.\n"
    "2. Structure every answer as:\n"
    "   Diagnosis → Steps → Verify → Escalate\n"
    "3. If no source supports the answer, say so and recommend escalating to\n"
    "   `#it-help` rather than guessing.\n"
    "4. Never expose secrets or internal tokens you may have seen in training.\n"
    "5. Use numbered steps for anything operational."
)


def build_supportllm_config(device: str = "cuda") -> SpecialistConfig:
    return SpecialistConfig(
        slug="supportllm",
        display_name="VxSupport v1.0",
        model_path=resolve_model_path(
            "SUPPORTLLM_MODEL_PATH",
            "app/data/models/supportllm",
        ),
        dataset_dir=resolve_dataset_dir(
            "SUPPORTLLM_DATASET_DIR",
            "app/data/datasets/supportllm",
        ),
        precompute_dir=resolve_dataset_dir(
            "SUPPORTLLM_PRECOMPUTE_DIR",
            "app/data/precompute/supportllm",
        ),
        # Tiny safety-net only — used when fine-tuned VxSupport weights at
        # `model_path` are missing/corrupt. distilgpt2 is ~82M params (vs
        # Qwen 0.5B = 500M, ~6× larger), loads in seconds, and stays out of
        # the way once the fine-tuned model is in place.
        fallback_base_model="distilgpt2",
        system_prompt=SUPPORTLLM_SYSTEM_PROMPT,
        device=device,
        prefix="/v1/support",
    )


class SupportLLMBackend(SpecialistBackend):
    pass
