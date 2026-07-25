"""Compatibility entry point for leakage-safe augmented PhoBERT training.

The historical implementation used stale ``data/final_*.csv`` paths and a
different single-seed, five-epoch protocol. Keep this filename for existing
users, but delegate to the canonical Round-5 multi-seed trainer so clean and
augmented comparisons use identical validation/test holdouts and settings.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    command = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "train_phobert_round5_multiseed.py"),
        "--train-file",
        str(PROJECT_DIR / "data" / "augmented_v2" / "final_train_augmented.csv"),
        "--seeds",
        "42",
        "123",
        "2024",
        "--result-name",
        "phobert_results_augmented.json",
        "--output-dir",
        str(PROJECT_DIR / "models" / "round5_predictions_augmented"),
    ]
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


if __name__ == "__main__":
    main()
