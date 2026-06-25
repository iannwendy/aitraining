"""Helpers for domain-adapted PhoBERT evaluation."""
import os
import subprocess
import sys
from pathlib import Path


def run_finetune(model_path: str, seed: int, output_dir: str) -> str:
    """Fine-tune a PhoBERT model on the final dataset.

    Returns path to the best checkpoint directory.

    The trainer (`phobert_train.train_phobert_first`) saves the best
    checkpoint directly to its `output_dir` argument via
    `model.save_pretrained(output_dir)` / `tokenizer.save_pretrained(output_dir)`
    whenever validation macro F1 improves (early-stopping tracking). There is
    no extra `best_model/` or `checkpoint-<N>/` subdirectory, so the override
    must point at `output_dir` itself.
    """
    os.environ["PHOBERT_MODEL_NAME_OVERRIDE"] = model_path
    os.environ["PHOBERT_OUTPUT_DIR_OVERRIDE"] = output_dir
    os.environ["PHOBERT_RANDOM_SEED_OVERRIDE"] = str(seed)

    script = (
        "from yt_depression_crawler.modeling.phobert.phobert_train import "
        "train_phobert_first; "
        "train_phobert_first()"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Fine-tune failed for {model_path} seed={seed}:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    # Trainer saves best weights straight to `output_dir` (no `best_model` subdir).
    # Accept either `output_dir` itself or a nested `best_model/` for forward-compat
    # in case the trainer is later refactored to nest.
    candidates = [output_dir, os.path.join(output_dir, "best_model")]
    expected = next((c for c in candidates if os.path.isdir(c)), None)
    if expected is None:
        raise RuntimeError(
            f"Expected checkpoint at one of {candidates} but none exist"
        )
    return expected