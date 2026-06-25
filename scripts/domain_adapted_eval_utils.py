"""Helpers for domain-adapted PhoBERT evaluation."""
import os
import subprocess
import sys
from pathlib import Path


def run_finetune(model_path: str, seed: int, output_dir: str) -> str:
    """Fine-tune a PhoBERT model on the final dataset.

    Returns path to the best checkpoint directory.
    """
    checkpoint_dir = os.path.join(output_dir, "checkpoints")
    os.environ["PHOBERT_MODEL_NAME_OVERRIDE"] = model_path
    os.environ["PHOBERT_OUTPUT_DIR_OVERRIDE"] = checkpoint_dir
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

    expected = os.path.join(checkpoint_dir, "best_model")
    if not os.path.isdir(expected):
        raise RuntimeError(
            f"Expected checkpoint at {expected} but directory does not exist"
        )
    return expected