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


def run_eval(checkpoint_dir: str, eval_csv: str, output_csv: str) -> None:
    """Run prediction on an eval CSV using a fine-tuned checkpoint.

    Writes predictions (comment_text, prob_normal, prob_depression,
    predicted_label) to output_csv.
    """
    import pandas as pd
    from yt_depression_crawler.modeling.phobert import phobert_predict

    df = pd.read_csv(eval_csv)
    if "comment_text" not in df.columns:
        raise ValueError(f"{eval_csv} must have a 'comment_text' column")

    texts = df["comment_text"].astype(str).tolist()
    preds = phobert_predict.predict_texts(
        texts=texts,
        model_dir=checkpoint_dir,
    )
    # preds is a list of dicts with keys: predicted_label, prob_normal, prob_depression
    out_df = pd.DataFrame({
        "comment_text": texts,
        "predicted_label": [p["predicted_label"] for p in preds],
        "prob_normal": [p["prob_normal"] for p in preds],
        "prob_depression": [p["prob_depression"] for p in preds],
    })
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_csv, index=False)


import json


def compute_cross_domain_metrics(pred_csv: str, gold_csv: str) -> dict:
    """Compute classification metrics for predictions joined with gold labels.

    Both CSVs are joined by row index (positional alignment).
    Returns a dict matching the metrics schema in the design spec.
    """
    import numpy as np
    import pandas as pd
    from yt_depression_crawler.modeling.phobert.phobert_utils import (
        compute_metrics as _compute_metrics,
    )

    preds = pd.read_csv(pred_csv)
    gold = pd.read_csv(gold_csv)
    if len(preds) != len(gold):
        raise ValueError(
            f"Row count mismatch: predictions={len(preds)} gold={len(gold)}"
        )

    y_true = gold["label"].astype(int).values
    y_pred = preds["predicted_label"].astype(int).values

    metrics = _compute_metrics(y_true, y_pred)
    return metrics


def aggregate_results(runs: list, output_dir: str, git_commit: str, timestamp: str) -> None:
    """Aggregate per-run metrics into metrics.json and comparison_table.md."""
    import statistics
    from collections import defaultdict

    metrics_path = os.path.join(output_dir, "metrics.json")
    table_path = os.path.join(output_dir, "comparison_table.md")

    payload = {
        "git_commit": git_commit,
        "timestamp": timestamp,
        "runs": runs,
    }
    with open(metrics_path, "w") as f:
        json.dump(payload, f, indent=2)

    # Group by (model_tag, test_set)
    groups = defaultdict(list)
    for r in runs:
        if r.get("status") == "failed":
            continue
        key = (r["model_tag"], r["test_set"])
        groups[key].append(r)

    lines = [
        "# Domain-Adapted PhoBERT Evaluation Results",
        "",
        f"Git commit: `{git_commit}`  ",
        f"Timestamp: `{timestamp}`",
        "",
        "| Model | Test set | n_seeds | Accuracy (mean+/-std) | "
        "F1 macro (mean+/-std) | F1 depression (mean+/-std) | "
        "Precision macro (mean+/-std) | Recall macro (mean+/-std) |",
        "|-------|----------|---------|------------------------|"
        "------------------------|-----------------------------|"
        "------------------------------|----------------------------|",
    ]

    def fmt(vals):
        if not vals:
            return "n/a"
        mean = statistics.mean(vals)
        if len(vals) < 2:
            return f"{mean:.4f} +/- n/a (n=1)"
        std = statistics.stdev(vals)
        return f"{mean:.4f} +/- {std:.4f}"

    for (model_tag, test_set), group in sorted(groups.items()):
        n = len(group)
        lines.append(
            f"| {model_tag} | {test_set} | {n} | "
            f"{fmt([g['accuracy'] for g in group])} | "
            f"{fmt([g['f1_macro'] for g in group])} | "
            f"{fmt([g['f1_depression'] for g in group])} | "
            f"{fmt([g['precision_macro'] for g in group])} | "
            f"{fmt([g['recall_macro'] for g in group])} |"
        )

    failed_count = sum(1 for r in runs if r.get("status") == "failed")
    lines.append("")
    lines.append(f"_Failed runs: {failed_count} / {len(runs)}_")
    lines.append("")

    with open(table_path, "w") as f:
        f.write("\n".join(lines))