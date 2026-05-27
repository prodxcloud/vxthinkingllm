"""Quick GPU sanity check on the freshly-trained VxThinking core.

Loads app/data/models/thinkingllm/ directly (not via SpecialistBackend, since
VxThinking has no system-prompt wrapper) and fires three prompts that should
hit content from the new soul.md / agent.md / skills.md / todos.md / changelogs.md.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    os.chdir(repo)
    model_dir = repo / "app/data/models/thinkingllm"

    if not (model_dir / "config.json").exists():
        print(f"!! No model at {model_dir}")
        return 1

    print(f"Loading {model_dir} ...")
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForCausalLM.from_pretrained(str(model_dir)).to("cuda")
    print(f"  loaded in {time.time() - t0:.1f}s on cuda")
    print(f"  arch: {model.config.architectures} | hidden={model.config.hidden_size} | vocab={model.config.vocab_size}")
    print()

    prompts = [
        "Who are you and what is your role at ProdxCloud?",
        "What's in flight this sprint? List the top 3 in-progress tickets.",
        "What endpoint do I call to provision a multi-cloud VM?",
    ]

    for p in prompts:
        print("=" * 72)
        print(f"PROMPT: {p}")
        inputs = tok(p, return_tensors="pt").to("cuda")
        t0 = time.time()
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=120,
                temperature=0.3,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tok.eos_token_id,
            )
        gen_ms = (time.time() - t0) * 1000
        text = tok.decode(out[0], skip_special_tokens=True)
        # Strip the echoed prompt so we only see the model's continuation
        if text.startswith(p):
            text = text[len(p):].lstrip()
        print(f"GEN ({gen_ms:.0f}ms):")
        print(text)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
