"""
CodingLLM training — VxCoder v1.0
==================================
Wrapper around the main VxThinkingLLM training loop, pointed at the
CodingLLM dataset folder.

QUICK START (from repo root):
    python -m app.services.ai.ml.codingllm.train --num-train-epochs 1
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from ..train import TrainConfig, LLM_MODEL_NAME, train
except ImportError:
    from app.services.ai.ml.train import TrainConfig, LLM_MODEL_NAME, train


DEFAULT_DATASET_DIR = Path("app") / "data" / "datasets" / "codingllm"
DEFAULT_OUTPUT_DIR = Path("app") / "data" / "models" / "codingllm"


def parse_args() -> TrainConfig:
    parser = argparse.ArgumentParser(description="Fine-tune VxCoder (CodingLLM)")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET_DIR))
    parser.add_argument(
        "--dataset-dir",
        type=str,
        nargs="?",
        const="",
        default=str(DEFAULT_DATASET_DIR),
    )
    parser.add_argument("--primary-csv", type=str, default="codingllm.csv")
    parser.add_argument(
        "--file-types",
        type=str,
        default="csv,json,txt,pdf,sql,xlsx,xls",
    )
    parser.add_argument("--model-name-or-path", type=str, default=LLM_MODEL_NAME)
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--text-max-length", type=int, default=1024)
    parser.add_argument("--per-device-train-batch-size", type=int, default=2)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    file_types = [ft.strip().lower() for ft in args.file_types.split(",") if ft.strip()]

    return TrainConfig(
        dataset_path=Path(args.dataset),
        dataset_dir=Path(args.dataset_dir) if args.dataset_dir else None,
        primary_csv=args.primary_csv,
        model_name_or_path=args.model_name_or_path,
        output_dir=Path(args.output_dir),
        text_max_length=args.text_max_length,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_train_epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        seed=args.seed,
        file_types=file_types,
    )


def main() -> None:
    cfg = parse_args()
    print(f"[CodingLLM] training -> {cfg.output_dir}")
    train(cfg)


if __name__ == "__main__":
    main()
