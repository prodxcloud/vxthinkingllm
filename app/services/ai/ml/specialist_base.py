"""
Specialist LLM Backend — shared base for CloudLLM / CodingLLM / SupportLLM.

Mirrors the load + generate pattern used by VxThinkingLLM in app/app.py:

    LOAD:
        tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        model = AutoModelForCausalLM.from_pretrained(str(model_dir)).to(device)

    GENERATE:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=..., temperature=...,
                                    top_p=..., do_sample=True,
                                    pad_token_id=tokenizer.eos_token_id)
        text = tokenizer.decode(output[0], skip_special_tokens=True)

There is NO vLLM, NO OpenAI-compatible client, NO httpx to a sidecar — the
model is invoked directly inside FastAPI, exactly as VxThinkingLLM does.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger("vallm.specialist")


@dataclass
class SpecialistConfig:
    """Per-model configuration (path, device, identity, system prompt).

    All model-specific knobs live here so method bodies stay pattern-identical
    across CloudLLM, CodingLLM, and SupportLLM.
    """

    slug: str                       # e.g. "cloudllm"
    display_name: str               # e.g. "VxCloud v1.0"
    model_path: Path                # trained weights dir (HF format, OUTPUT of training)
    fallback_base_model: str        # HF id to pull if model_path is empty
    system_prompt: str
    device: str = "cuda"            # overridden if CUDA not available
    prefix: str = ""                # e.g. "/v1/cloud"
    dataset_dir: Optional[Path] = None     # INPUT of training (auto-resolved)
    precompute_dir: Optional[Path] = None  # optional side-index output


class SpecialistBackend:
    """Direct in-process HF causal LM backend.

    Intentionally mirrors VxThinkingLLM's load/generate behavior line-for-line
    so routing-level code stays symmetric across all four models.
    """

    def __init__(self, cfg: SpecialistConfig):
        self.cfg = cfg
        self.tokenizer = None
        self.model = None
        self.loaded = False
        self.effective_device = "cpu"
        self.loaded_from: Optional[str] = None

    def describe_paths(self) -> Dict[str, str]:
        """Return the resolved filesystem paths this backend will read/write.

        Used in /health responses and logged once at load() so operators can
        sanity-check that the model is pointing at the right dataset/output dir.
        """
        return {
            "model_path":     str(self.cfg.model_path),
            "dataset_dir":    str(self.cfg.dataset_dir) if self.cfg.dataset_dir else "",
            "precompute_dir": str(self.cfg.precompute_dir) if self.cfg.precompute_dir else "",
            "prefix":         self.cfg.prefix,
        }

    def load(self) -> None:
        """Load tokenizer + weights into memory.

        Tries `cfg.model_path` first (fine-tuned specialist weights). If that's
        empty or invalid, falls back to `cfg.fallback_base_model` so the route
        is still serviceable before training has been run.
        """
        desired = self.cfg.device
        self.effective_device = "cuda" if (desired == "cuda" and torch.cuda.is_available()) else "cpu"

        logger.info(
            "%s resolving paths | model_path=%s dataset_dir=%s precompute_dir=%s prefix=%s",
            self.cfg.slug,
            self.cfg.model_path,
            self.cfg.dataset_dir or "<none>",
            self.cfg.precompute_dir or "<none>",
            self.cfg.prefix,
        )

        tried: list[str] = []
        model_dir = self.cfg.model_path
        config_json = model_dir / "config.json"

        if config_json.exists():
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                self.model = AutoModelForCausalLM.from_pretrained(str(model_dir)).to(self.effective_device)
                self.loaded = True
                self.loaded_from = str(model_dir)
                logger.info("%s loaded specialist weights from %s (device=%s)",
                            self.cfg.slug, model_dir, self.effective_device)
                return
            except Exception as e:  # pragma: no cover - soft-fail to base model
                tried.append(f"{model_dir} -> {e}")
                logger.warning("%s failed to load %s: %s", self.cfg.slug, model_dir, e)

        # Fallback: HuggingFace base model (network-free if already cached)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.cfg.fallback_base_model)
            self.model = AutoModelForCausalLM.from_pretrained(self.cfg.fallback_base_model).to(self.effective_device)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.model.config.pad_token_id = self.tokenizer.eos_token_id
            self.loaded = True
            self.loaded_from = self.cfg.fallback_base_model
            logger.info("%s loaded fallback base model %s (device=%s)",
                        self.cfg.slug, self.cfg.fallback_base_model, self.effective_device)
        except Exception as e:
            tried.append(f"{self.cfg.fallback_base_model} -> {e}")
            logger.warning("%s could not load any model. Tried: %s", self.cfg.slug, tried)
            self.loaded = False

    def build_prompt(self, user_prompt: str, context: Optional[Dict] = None) -> str:
        """Prepend the baked-in system prompt. Keeps generation grounded."""
        ctx_str = ""
        if context:
            try:
                import json as _json
                ctx_str = f"\n### Context\n{_json.dumps(context, ensure_ascii=False)[:2000]}\n"
            except Exception:
                ctx_str = ""
        return (
            f"### System\n{self.cfg.system_prompt}\n"
            f"{ctx_str}"
            f"### User\n{user_prompt}\n"
            f"### Response\n"
        )

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 400,
        temperature: float = 0.3,
        top_p: float = 0.9,
        context: Optional[Dict] = None,
    ) -> Dict[str, object]:
        """Run the model. Mirrors VxThinkingLLM's /generate handler exactly."""
        if not self.loaded or self.tokenizer is None or self.model is None:
            return {
                "response": f"{self.cfg.display_name} not loaded. Run training or set {self.cfg.slug.upper()}_MODEL_PATH.",
                "model_loaded": False,
                "device": "none",
                "model_name": self.cfg.display_name,
            }

        full_prompt = self.build_prompt(prompt, context=context)
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.effective_device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True)
        # Strip the prompt prefix if the tokenizer echoed it back (common with
        # causal LMs — same behavior VxThinkingLLM documents in /generate).
        answer = decoded[len(full_prompt):] if decoded.startswith(full_prompt) else decoded
        answer = answer.strip()

        return {
            "response": answer,
            "raw": decoded,
            "model_loaded": True,
            "device": self.effective_device,
            "model_name": self.cfg.display_name,
            "loaded_from": self.loaded_from,
        }


def _repo_root() -> Path:
    """Resolve the project root (parent of the `app` package).

    specialist_base.py lives at
      <repo>/app/services/ai/ml/specialist_base.py
    so parents[4] == <repo>.
    """
    return Path(__file__).resolve().parents[4]


def resolve_model_path(env_var: str, default_relative: str) -> Path:
    """Resolve an absolute weights path from env or a repo-relative default."""
    raw = os.getenv(env_var)
    if raw:
        return Path(raw).resolve()
    return (_repo_root() / default_relative).resolve()


def resolve_dataset_dir(env_var: str, default_relative: str) -> Path:
    """Resolve the training dataset directory from env or the default convention
    (`app/data/datasets/<slug>`). Guaranteed to return an absolute path even if
    the folder doesn't exist yet — the train wrapper will create it."""
    raw = os.getenv(env_var)
    if raw:
        return Path(raw).resolve()
    return (_repo_root() / default_relative).resolve()
