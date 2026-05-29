"""
Fine-tune the CloudLLM on the datasets under `app/data/datasets/`.

Writes weights + tokenizer to `app/data/models/` so the FastAPI app picks them
up at startup.

Run from repo root:
    python -m app.services.ai.ml.train --num-train-epochs 1
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("vxcloud.train")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


DEFAULT_DATASETS_DIR = _repo_root() / "app" / "data" / "datasets"
DEFAULT_OUTPUT_DIR = _repo_root() / "app" / "data" / "models"
LLM_MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
SUPPORTED_SUFFIXES = {".csv", ".txt", ".md", ".json"}


@dataclass
class TrainConfig:
    datasets_dir: Path = DEFAULT_DATASETS_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    model_name_or_path: str = LLM_MODEL_NAME
    text_max_length: int = 512
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_train_epochs: float = 1.0
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    seed: int = 42
    file_types: List[str] = field(default_factory=lambda: ["csv", "json", "txt", "md"])


def _row_to_text(row: dict) -> str:
    return " | ".join(f"{k}: {v}" for k, v in row.items() if v not in (None, ""))


def _read_csv(path: Path) -> List[str]:
    out: List[str] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            text = _row_to_text(row).strip()
            if text:
                out.append(text)
    return out


def _read_text(path: Path) -> List[str]:
    body = path.read_text(encoding="utf-8", errors="replace")
    chunks = [c.strip() for c in body.split("\n\n") if c.strip()]
    return chunks or ([body.strip()] if body.strip() else [])


def _read_json(path: Path) -> List[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.warning("Skipping %s (invalid JSON: %s)", path.name, e)
        return []
    if isinstance(data, list):
        return [json.dumps(item, ensure_ascii=False) for item in data]
    if isinstance(data, dict):
        return [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in data.items()]
    return [str(data)]


def load_texts(cfg: TrainConfig) -> List[str]:
    if not cfg.datasets_dir.exists():
        raise FileNotFoundError(f"Datasets dir does not exist: {cfg.datasets_dir}")

    accepted = {f".{t.lower().lstrip('.')}" for t in cfg.file_types} & SUPPORTED_SUFFIXES
    texts: List[str] = []
    for path in sorted(p for p in cfg.datasets_dir.iterdir() if p.is_file() and p.suffix.lower() in accepted):
        suffix = path.suffix.lower()
        if suffix == ".csv":
            file_texts = _read_csv(path)
        elif suffix == ".json":
            file_texts = _read_json(path)
        else:
            file_texts = _read_text(path)
        logger.info("  %s → %d examples", path.name, len(file_texts))
        texts.extend(file_texts)
    return texts


def train(cfg: TrainConfig) -> None:
    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    set_seed(cfg.seed)

    texts = load_texts(cfg)
    if not texts:
        raise RuntimeError(f"No training examples found in {cfg.datasets_dir}")
    logger.info("Total examples: %d", len(texts))

    logger.info("Loading tokenizer + base model %s", cfg.model_name_or_path)
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg.model_name_or_path)
    model.config.pad_token_id = tokenizer.pad_token_id

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            max_length=cfg.text_max_length,
            truncation=True,
            padding=False,
        )

    ds = Dataset.from_dict({"text": texts})
    ds = ds.map(tokenize, batched=True, remove_columns=["text"], desc="Tokenizing")

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(cfg.output_dir / "_checkpoints"),
        overwrite_output_dir=True,
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        num_train_epochs=cfg.num_train_epochs,
        learning_rate=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
        warmup_ratio=cfg.warmup_ratio,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=1,
        report_to=[],
        seed=cfg.seed,
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=ds,
        data_collator=collator,
        tokenizer=tokenizer,
    )

    logger.info("Starting training → %s", cfg.output_dir)
    trainer.train()

    logger.info("Saving model + tokenizer → %s", cfg.output_dir)
    trainer.save_model(str(cfg.output_dir))
    tokenizer.save_pretrained(str(cfg.output_dir))
    logger.info("Done.")


def parse_args(argv: List[str] | None = None) -> TrainConfig:
    parser = argparse.ArgumentParser(description="Fine-tune the CloudLLM")
    parser.add_argument("--datasets-dir", type=Path, default=DEFAULT_DATASETS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model-name-or-path", type=str, default=LLM_MODEL_NAME)
    parser.add_argument("--text-max-length", type=int, default=512)
    parser.add_argument("--per-device-train-batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--file-types", type=str, default="csv,json,txt,md")
    args = parser.parse_args(argv)

    file_types = [ft.strip().lower() for ft in args.file_types.split(",") if ft.strip()]
    return TrainConfig(
        datasets_dir=args.datasets_dir,
        output_dir=args.output_dir,
        model_name_or_path=args.model_name_or_path,
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


def main(argv: List[str] | None = None) -> int:
    cfg = parse_args(argv)
    train(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
