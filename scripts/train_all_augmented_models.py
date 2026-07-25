"""Run the canonical augmented-data experiments without holdout leakage.

This replaces the legacy script that combined validation with training and
read obsolete ``data/augmented_version`` files. Every command below uses the
same fixed human-only validation/test splits and the unchanged VSMEC proxy
holdout used by the clean-data experiments.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TRAIN_FILE = PROJECT_DIR / "data" / "augmented_v2" / "final_train_augmented.csv"
PHOBERT_OUTPUT = PROJECT_DIR / "models" / "round5_predictions_augmented"


def run(*args: str) -> None:
    subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_DIR,
        check=True,
        env={**__import__("os").environ, "PYTHONPATH": str(PROJECT_DIR)},
    )


def main() -> None:
    run(
        "scripts/train_evaluate_classical.py",
        "--train-file", str(TRAIN_FILE),
        "--tag", "augmented",
    )
    run(
        "scripts/run_bilstm_multiseed.py",
        "--seeds", "42", "123", "2024",
        "--variants", "random", "phobert",
        "--train-file", str(TRAIN_FILE),
        "--tag", "augmented",
    )
    run(
        "scripts/train_phobert_round5_multiseed.py",
        "--train-file", str(TRAIN_FILE),
        "--seeds", "42", "123", "2024",
        "--result-name", "phobert_results_augmented.json",
        "--output-dir", str(PHOBERT_OUTPUT),
    )
    run(
        "scripts/rerun_phobert_bertopic.py",
        "--train-file", str(TRAIN_FILE),
        "--phobert-dir", str(PHOBERT_OUTPUT / "seed_42" / "best_model"),
        "--tag", "augmented",
    )


if __name__ == "__main__":
    main()
