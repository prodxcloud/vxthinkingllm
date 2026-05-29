"""CloudLLMBackend — VxCloud DevOps / IaC / SRE specialist."""

from __future__ import annotations

try:
    from .specialist_base import (
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


CLOUDLLM_SYSTEM_PROMPT = (
    "You are VxCloud, an expert DevOps / SRE / Cloud engineer. "
    "You specialize in Terraform, Kubernetes, Ansible, Helm, Dockerfiles, "
    "cloud incident runbooks, and cost optimization.\n\n"
    "Hard rules:\n"
    "1. Always output valid, runnable code with inline comments.\n"
    "2. Flag every security-relevant line with a `# SECURITY:` comment.\n"
    "3. Always include CPU/memory `resources.limits` in Kubernetes manifests.\n"
    "4. Prefer least-privilege IAM; never use wildcards in policies.\n"
    "5. If a request is not DevOps/cloud, say so and suggest the right model."
)


def build_cloudllm_config(device: str = "cuda") -> SpecialistConfig:
    return SpecialistConfig(
        slug="cloudllm",
        display_name="VxCloud v1.0",
        model_path=resolve_model_path("CLOUDLLM_MODEL_PATH", "app/data/models"),
        dataset_dir=resolve_dataset_dir("CLOUDLLM_DATASET_DIR", "app/data/datasets"),
        fallback_base_model="Qwen/Qwen2.5-0.5B-Instruct",
        system_prompt=CLOUDLLM_SYSTEM_PROMPT,
        device=device,
        prefix="/v1/model",
    )


class CloudLLMBackend(SpecialistBackend):
    """Alias class so type hints and logs show `CloudLLMBackend` explicitly."""
    pass
