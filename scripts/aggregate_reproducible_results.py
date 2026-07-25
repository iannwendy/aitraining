"""Aggregate the repaired Round-5 experiments into canonical artifacts.

The script keeps three quantities distinct:

* multi-seed mean/std for stochastic model-family comparisons;
* point estimates for deterministic models and PhoBERT majority voting;
* a clearly named reference prediction run when a confusion matrix is needed.

It also computes stratified bootstrap confidence intervals and paired clean vs
augmented McNemar tests from row-level predictions. No result is read from the
historical ``results/round*`` directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
import torch
import transformers
from scipy.stats import binomtest
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results" / "reproducible_round5"
METRIC_KEYS = [
    "accuracy",
    "precision_macro",
    "recall_macro",
    "f1_macro",
    "f1_weighted",
    "f1_depression",
]
DOMAINS = ["in_domain", "cross_domain"]
BOOTSTRAP_SEED = 42
BOOTSTRAP_ITERATIONS = 2_000


def read_json(path: Path, *, required: bool = True) -> dict | None:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def point_metric_block(metrics: dict) -> dict:
    return {
        key: {"mean": float(metrics[key]), "std": None, "per_seed": None}
        for key in METRIC_KEYS
    }


def normalize_metric_block(metrics: dict) -> dict:
    block = {}
    for key in METRIC_KEYS:
        value = metrics[key]
        if isinstance(value, dict) and "mean" in value:
            std_value = value.get("std")
            block[key] = {
                "mean": float(value["mean"]),
                "std": float(std_value) if std_value is not None else None,
                "per_seed": value.get("per_seed"),
            }
        else:
            block[key] = {"mean": float(value), "std": None, "per_seed": None}
    return block


def add_model(
    rows: list[dict],
    *,
    tag: str,
    model_id: str,
    display_name: str,
    domains: dict[str, dict],
    n_seeds: int,
    estimate_type: str,
    reference_prediction: str | None = None,
) -> None:
    rows.append({
        "tag": tag,
        "model_id": model_id,
        "display_name": display_name,
        "n_seeds": n_seeds,
        "estimate_type": estimate_type,
        "reference_prediction": reference_prediction,
        "domains": {
            domain: normalize_metric_block(domains[domain])
            for domain in DOMAINS
        },
    })


def aggregate_models(*, allow_missing: bool) -> tuple[list[dict], dict | None]:
    rows: list[dict] = []
    for tag in ["clean", "augmented"]:
        classical = read_json(
            RESULTS_DIR / f"classical_results_{tag}.json",
            required=not allow_missing,
        )
        if classical:
            for model_id, display_name in [
                ("tfidf_logreg", "TF-IDF + Logistic Regression"),
                ("tfidf_linearsvc", "TF-IDF + LinearSVC"),
            ]:
                add_model(
                    rows,
                    tag=tag,
                    model_id=model_id,
                    display_name=display_name,
                    domains=classical["models"][model_id],
                    n_seeds=1,
                    estimate_type="single deterministic run",
                    reference_prediction="same run",
                )

        phobert = read_json(
            RESULTS_DIR / f"phobert_results_{tag}.json",
            required=not allow_missing,
        )
        if phobert:
            add_model(
                rows,
                tag=tag,
                model_id="phobert_mean",
                display_name="PhoBERT",
                domains=phobert["mean_std"],
                n_seeds=len(phobert["seeds"]),
                estimate_type="multi-seed mean/std",
                reference_prediction="seed 42 (confusion matrices only)",
            )
            add_model(
                rows,
                tag=tag,
                model_id="phobert_majority_vote",
                display_name="PhoBERT majority vote",
                domains={
                    domain: point_metric_block(phobert["ensemble_majority_vote"][domain])
                    for domain in DOMAINS
                },
                n_seeds=len(phobert["seeds"]),
                estimate_type="majority-vote point estimate",
                reference_prediction="majority vote",
            )

        bilstm = read_json(
            RESULTS_DIR / f"bilstm_results_{tag}.json",
            required=not allow_missing,
        )
        if bilstm:
            for variant, display_name in [
                ("random", "BiLSTM (random embeddings)"),
                ("phobert", "BiLSTM (frozen PhoBERT embeddings)"),
            ]:
                source = bilstm["variants"][variant]
                add_model(
                    rows,
                    tag=tag,
                    model_id=f"bilstm_{variant}",
                    display_name=display_name,
                    domains={
                        "in_domain": source["test"],
                        "cross_domain": source["cross_domain_vsmec"],
                    },
                    n_seeds=source["n_seeds"],
                    estimate_type="multi-seed mean/std",
                    reference_prediction="seed 42 (confusion matrices only)",
                )

        topic = read_json(
            RESULTS_DIR / f"topic_models_results_{tag}.json",
            required=not allow_missing,
        )
        if topic:
            add_model(
                rows,
                tag=tag,
                model_id="bertopic_only",
                display_name="BERTopic-only + Logistic Regression",
                domains=topic["bertopic_only"],
                n_seeds=1,
                estimate_type="single deterministic run",
                reference_prediction="same run",
            )
            add_model(
                rows,
                tag=tag,
                model_id="phobert_bertopic",
                display_name="PhoBERT + BERTopic",
                domains={domain: topic[domain] for domain in DOMAINS},
                n_seeds=1,
                estimate_type="single seed-42 feature model",
                reference_prediction="same run",
            )

    selected = read_json(
        RESULTS_DIR / "validation_selected_ensemble_results.json", required=False
    )
    if selected:
        selection = selected["selection"]
        add_model(
            rows,
            tag="selected",
            model_id="validation_selected_ensemble",
            display_name=f"Validation-selected final model ({selection['name']})",
            domains=selected["splits"],
            n_seeds=1,
            estimate_type=(
                f"locked validation-only threshold={float(selection['threshold']):.2f}"
            ),
            reference_prediction="same locked run",
        )

    dapt = read_json(RESULTS_DIR / "dapt" / "metrics.json", required=False)
    return rows, dapt


def read_predictions(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    label_col = next((c for c in ["label", "true_label"] if c in frame.columns), None)
    pred_col = next((c for c in ["prediction", "pred_label", "predicted_label"] if c in frame.columns), None)
    if label_col is None or pred_col is None or "comment_text" not in frame.columns:
        raise ValueError(f"Unsupported prediction schema in {path}: {frame.columns.tolist()}")
    result = frame[["comment_text", label_col, pred_col]].rename(
        columns={label_col: "label", pred_col: "prediction"}
    )
    result["label"] = result["label"].astype(int)
    result["prediction"] = result["prediction"].astype(int)
    if result["comment_text"].duplicated().any():
        raise ValueError(f"Duplicate comment_text in {path}")
    return result


def phobert_ensemble(tag: str, domain: str) -> pd.DataFrame:
    frames = []
    for seed in [42, 123, 2024]:
        path = RESULTS_DIR / f"phobert_{tag}_seed{seed}_{domain}_predictions.csv"
        frame = read_predictions(path).rename(columns={"prediction": f"prediction_{seed}"})
        frames.append(frame)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=["comment_text", "label"], validate="one_to_one")
    prediction_cols = [f"prediction_{seed}" for seed in [42, 123, 2024]]
    merged["prediction"] = (merged[prediction_cols].mean(axis=1) >= 0.5).astype(int)
    output = merged[["comment_text", "label", "prediction"]]
    output.to_csv(RESULTS_DIR / f"phobert_{tag}_majority_vote_{domain}_predictions.csv", index=False)
    return output


def prediction_registry(*, allow_missing: bool) -> dict[tuple[str, str, str], pd.DataFrame]:
    registry: dict[tuple[str, str, str], pd.DataFrame] = {}
    for tag in ["clean", "augmented"]:
        paths = {
            "tfidf_logreg": {
                domain: RESULTS_DIR / f"tfidf_logreg_{tag}_{domain}_predictions.csv"
                for domain in DOMAINS
            },
            "tfidf_linearsvc": {
                domain: RESULTS_DIR / f"tfidf_linearsvc_{tag}_{domain}_predictions.csv"
                for domain in DOMAINS
            },
            "bilstm_random": {
                "in_domain": PROJECT_DIR / "models" / f"bilstm_round5_{tag}" / "random" / "seed_42" / "in_domain_predictions.csv",
                "cross_domain": PROJECT_DIR / "models" / f"bilstm_round5_{tag}" / "random" / "seed_42" / "cross_domain_predictions.csv",
            },
            "bilstm_phobert": {
                "in_domain": PROJECT_DIR / "models" / f"bilstm_round5_{tag}" / "phobert" / "seed_42" / "in_domain_predictions.csv",
                "cross_domain": PROJECT_DIR / "models" / f"bilstm_round5_{tag}" / "phobert" / "seed_42" / "cross_domain_predictions.csv",
            },
            "bertopic_only": {
                domain: RESULTS_DIR / f"bertopic_only_{tag}_predictions_{domain}.csv"
                for domain in DOMAINS
            },
            "phobert_bertopic": {
                domain: RESULTS_DIR / f"phobert_bertopic_{tag}_predictions_{domain}.csv"
                for domain in DOMAINS
            },
        }
        for model_id, by_domain in paths.items():
            for domain, path in by_domain.items():
                if path.exists():
                    registry[(tag, model_id, domain)] = read_predictions(path)
                elif not allow_missing:
                    raise FileNotFoundError(path)
        phobert_files_exist = all(
            (RESULTS_DIR / f"phobert_{tag}_seed{seed}_{domain}_predictions.csv").exists()
            for seed in [42, 123, 2024]
            for domain in DOMAINS
        )
        if phobert_files_exist:
            for domain in DOMAINS:
                ensemble = phobert_ensemble(tag, domain)
                registry[(tag, "phobert_majority_vote", domain)] = ensemble
                seed42 = read_predictions(
                    RESULTS_DIR / f"phobert_{tag}_seed42_{domain}_predictions.csv"
                )
                registry[(tag, "phobert_mean", domain)] = seed42
        elif not allow_missing:
            raise FileNotFoundError(f"Missing PhoBERT prediction files for {tag}")
    selected_paths = {
        domain: RESULTS_DIR / f"validation_selected_ensemble_{domain}_predictions.csv"
        for domain in DOMAINS
    }
    if all(path.exists() for path in selected_paths.values()):
        for domain, path in selected_paths.items():
            registry[("selected", "validation_selected_ensemble", domain)] = read_predictions(path)
    return registry


def metrics_from_predictions(frame: pd.DataFrame) -> dict:
    y_true = frame["label"].to_numpy()
    y_pred = frame["prediction"].to_numpy()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_depression": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def stratified_bootstrap_indices(labels: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    parts = []
    for label in sorted(np.unique(labels)):
        indices = np.flatnonzero(labels == label)
        parts.append(rng.choice(indices, size=len(indices), replace=True))
    return np.concatenate(parts)


def bootstrap_f1_ci(frame: pd.DataFrame) -> dict:
    labels = frame["label"].to_numpy()
    predictions = frame["prediction"].to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples = np.empty(BOOTSTRAP_ITERATIONS, dtype=float)
    for i in range(BOOTSTRAP_ITERATIONS):
        indices = stratified_bootstrap_indices(labels, rng)
        samples[i] = f1_score(labels[indices], predictions[indices], average="macro", zero_division=0)
    return {
        "estimate": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "ci_95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "method": f"stratified percentile bootstrap, {BOOTSTRAP_ITERATIONS} resamples",
        "seed": BOOTSTRAP_SEED,
    }


def paired_clean_augmented(clean: pd.DataFrame, augmented: pd.DataFrame) -> dict:
    merged = clean.merge(
        augmented,
        on=["comment_text", "label"],
        suffixes=("_clean", "_augmented"),
        validate="one_to_one",
    )
    if len(merged) != len(clean) or len(merged) != len(augmented):
        raise ValueError("Clean and augmented predictions do not cover identical rows")
    labels = merged["label"].to_numpy()
    clean_pred = merged["prediction_clean"].to_numpy()
    augmented_pred = merged["prediction_augmented"].to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    deltas = np.empty(BOOTSTRAP_ITERATIONS, dtype=float)
    for i in range(BOOTSTRAP_ITERATIONS):
        indices = stratified_bootstrap_indices(labels, rng)
        clean_f1 = f1_score(labels[indices], clean_pred[indices], average="macro", zero_division=0)
        augmented_f1 = f1_score(labels[indices], augmented_pred[indices], average="macro", zero_division=0)
        deltas[i] = augmented_f1 - clean_f1

    clean_correct = clean_pred == labels
    augmented_correct = augmented_pred == labels
    clean_only = int(np.sum(clean_correct & ~augmented_correct))
    augmented_only = int(np.sum(~clean_correct & augmented_correct))
    discordant = clean_only + augmented_only
    p_value = float(
        binomtest(clean_only, discordant, p=0.5, alternative="two-sided").pvalue
        if discordant else 1.0
    )
    return {
        "rows": len(merged),
        "clean_f1_macro": float(f1_score(labels, clean_pred, average="macro", zero_division=0)),
        "augmented_f1_macro": float(f1_score(labels, augmented_pred, average="macro", zero_division=0)),
        "delta_augmented_minus_clean": float(
            f1_score(labels, augmented_pred, average="macro", zero_division=0)
            - f1_score(labels, clean_pred, average="macro", zero_division=0)
        ),
        "delta_ci_95": [float(np.quantile(deltas, 0.025)), float(np.quantile(deltas, 0.975))],
        "mcnemar_exact": {
            "clean_correct_augmented_wrong": clean_only,
            "clean_wrong_augmented_correct": augmented_only,
            "p_value": p_value,
        },
    }


def holm_adjust(records: list[tuple[dict, float]]) -> None:
    ordered = sorted(enumerate(records), key=lambda item: item[1][1])
    adjusted = [1.0] * len(records)
    running = 0.0
    total = len(records)
    for rank, (original_index, (_, p_value)) in enumerate(ordered):
        candidate = min(1.0, (total - rank) * p_value)
        running = max(running, candidate)
        adjusted[original_index] = running
    for (record, _), value in zip(records, adjusted):
        record["mcnemar_exact"]["p_value_holm"] = float(value)


def build_prediction_analyses(registry: dict) -> tuple[dict, dict]:
    confusion_payload: dict[str, dict] = defaultdict(dict)
    ci_payload: dict[str, dict] = defaultdict(dict)
    for (tag, model_id, domain), frame in sorted(registry.items()):
        metrics = metrics_from_predictions(frame)
        confusion_payload[tag][f"{model_id}:{domain}"] = {
            "rows": len(frame),
            "matrix_order": [["true_normal", "pred_normal"], ["true_depression", "pred_depression"]],
            "confusion_matrix": metrics["confusion_matrix"],
            "f1_macro": metrics["f1_macro"],
        }
        ci_payload[tag][f"{model_id}:{domain}"] = bootstrap_f1_ci(frame)

    comparisons: dict[str, dict] = defaultdict(dict)
    holm_by_domain: dict[str, list[tuple[dict, float]]] = defaultdict(list)
    model_ids = sorted({model_id for tag, model_id, domain in registry if tag == "clean"})
    for model_id in model_ids:
        for domain in DOMAINS:
            clean_key = ("clean", model_id, domain)
            augmented_key = ("augmented", model_id, domain)
            if clean_key not in registry or augmented_key not in registry:
                continue
            record = paired_clean_augmented(registry[clean_key], registry[augmented_key])
            comparisons[model_id][domain] = record
            holm_by_domain[domain].append((record, record["mcnemar_exact"]["p_value"]))
    for records in holm_by_domain.values():
        holm_adjust(records)
    return {
        "bootstrap_f1_macro": ci_payload,
        "clean_vs_augmented": comparisons,
    }, confusion_payload


def summarize_dapt(raw: dict | None) -> dict | None:
    if not raw:
        return None
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for run in raw.get("runs", []):
        if run.get("status") == "ok" and "test_set" in run:
            groups[(run["model_tag"], run["test_set"])].append(run)
    summary = {}
    for (model_tag, test_set), runs in sorted(groups.items()):
        group_summary = {
            key: {
                "mean": float(np.mean([run[key] for run in runs])),
                "std": float(np.std([run[key] for run in runs], ddof=1)) if len(runs) > 1 else None,
                "per_seed": {str(run["seed"]): float(run[key]) for run in runs},
            }
            for key in METRIC_KEYS
        }
        group_summary["n_seeds"] = len(runs)
        summary[f"{model_tag}:{test_set}"] = group_summary
    for test_set in ["final_test", "vsmec"]:
        original = summary.get(f"original:{test_set}")
        adapted = summary.get(f"domain_adapted:{test_set}")
        if original and adapted:
            summary[f"delta_domain_adapted_minus_original:{test_set}"] = {
                key: adapted[key]["mean"] - original[key]["mean"]
                for key in METRIC_KEYS
            }
    return summary


def fmt_metric(metric: dict) -> str:
    if metric["std"] is None:
        return f"{metric['mean']:.4f}"
    return f"{metric['mean']:.4f} ± {metric['std']:.4f}"


def write_model_table(rows: list[dict]) -> None:
    lines = [
        "# Canonical model comparison",
        "",
        "Primary metric: macro-F1. VSMEC is an affective cross-domain proxy, not a clinical depression gold standard.",
        "",
    ]
    section_titles = {
        "clean": "Clean training data",
        "augmented": "Augmented training data",
        "selected": "Validation-selected final model",
    }
    for tag in ["clean", "augmented", "selected"]:
        tag_rows = [item for item in rows if item["tag"] == tag]
        if not tag_rows:
            continue
        lines.extend([
            f"## {section_titles[tag]}",
            "",
            "| Model | Estimate | n seeds | Domain | Accuracy | Precision-M | Recall-M | F1-M | F1-W | F1-Dep |",
            "|---|---|---:|---|---:|---:|---:|---:|---:|---:|",
        ])
        for row in tag_rows:
            for domain in DOMAINS:
                metrics = row["domains"][domain]
                lines.append(
                    f"| {row['display_name']} | {row['estimate_type']} | {row['n_seeds']} | "
                    f"{domain.replace('_', '-')} | "
                    + " | ".join(fmt_metric(metrics[key]) for key in METRIC_KEYS)
                    + " |"
                )
        lines.append("")
    (RESULTS_DIR / "model_comparison.md").write_text("\n".join(lines), encoding="utf-8")


def reproducibility_manifest(result_paths: list[Path]) -> dict:
    datasets = [
        PROJECT_DIR / "data" / "labeled" / "final_train.csv",
        PROJECT_DIR / "data" / "labeled" / "final_val.csv",
        PROJECT_DIR / "data" / "labeled" / "final_test.csv",
        PROJECT_DIR / "data" / "augmented_v2" / "final_train_augmented.csv",
        PROJECT_DIR / "data_unified" / "cross_domain_test.csv",
    ]
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_DIR, text=True
        ).strip()
    except Exception:
        commit = "unknown"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
        "datasets": {
            str(path.relative_to(PROJECT_DIR)): {
                "rows": int(len(pd.read_csv(path))),
                "sha256": sha256_file(path),
            }
            for path in datasets
            if path.exists()
        },
        "result_artifacts": {
            str(path.relative_to(PROJECT_DIR)): sha256_file(path)
            for path in result_paths
            if path.exists()
        },
        "canonical_commands": [
            "PYTHONPATH=$PWD .venv/bin/python scripts/merge_round5_reviewed.py",
            "PYTHONPATH=$PWD .venv/bin/python scripts/data_augmentation.py --input data/labeled/final_train.csv --output data/augmented_v2/generated_depression_train.csv --depression-only --n-augment 3",
            "PYTHONPATH=$PWD .venv/bin/python scripts/merge_augmented.py",
            "PYTHONPATH=$PWD .venv/bin/python scripts/train_evaluate_classical.py --tag clean",
            "PYTHONPATH=$PWD .venv/bin/python scripts/train_phobert_round5_multiseed.py --seeds 42 123 2024 --result-name phobert_results_clean.json --output-dir models/round5_predictions_clean",
            "PYTHONPATH=$PWD .venv/bin/python scripts/export_phobert_predictions.py --model-root models/round5_predictions_clean --tag clean --seeds 42 123 2024 --splits validation",
            "PYTHONPATH=$PWD .venv/bin/python scripts/run_bilstm_multiseed.py --seeds 42 123 2024 --variants random phobert --tag clean",
            "PYTHONPATH=$PWD .venv/bin/python -m scripts.evaluate_domain_adapted_phobert --models models/phobert_base_local models/phobert_domain_adapted --seeds 42 123 2024 --output-dir results/reproducible_round5/dapt",
            "Repeat model commands with data/augmented_v2/final_train_augmented.csv and tag=augmented",
            "PYTHONPATH=$PWD .venv/bin/python scripts/select_validation_ensemble.py tune",
            "PYTHONPATH=$PWD .venv/bin/python scripts/select_validation_ensemble.py evaluate",
            "PYTHONPATH=$PWD .venv/bin/python scripts/aggregate_reproducible_results.py",
            ".venv/bin/pytest -q",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rows, dapt_raw = aggregate_models(allow_missing=args.allow_missing)
    registry = prediction_registry(allow_missing=args.allow_missing)
    statistics_payload, confusion_payload = build_prediction_analyses(registry)
    dapt_summary = summarize_dapt(dapt_raw)

    canonical = {
        "protocol": {
            "training": "train split only; validation for model selection; test sets transform/evaluate only",
            "final_model_selection": "weights and threshold locked on validation before one-time holdout evaluation",
            "in_domain": "fixed human-only test split",
            "cross_domain": "VSMEC Sadness/Fear vs Enjoyment affective proxy; non-clinical",
            "primary_metric": "macro F1",
        },
        "models": rows,
        "dapt": dapt_summary,
        "statistics": statistics_payload,
    }
    canonical_path = RESULTS_DIR / "canonical_results.json"
    confusion_path = RESULTS_DIR / "confusion_matrices.json"
    statistics_path = RESULTS_DIR / "statistical_tests.json"
    canonical_path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")
    confusion_path.write_text(json.dumps(confusion_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    statistics_path.write_text(json.dumps(statistics_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_model_table(rows)

    input_results = [
        path
        for path in sorted(RESULTS_DIR.glob("*.json"))
        if path.name != "reproducibility_manifest.json"
    ] + sorted((RESULTS_DIR / "dapt").glob("*.json"))
    manifest = reproducibility_manifest(input_results)
    manifest_path = RESULTS_DIR / "reproducibility_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved canonical results: {canonical_path}")
    print(f"Saved confusion matrices: {confusion_path}")
    print(f"Saved statistical tests: {statistics_path}")
    print(f"Saved reproducibility manifest: {manifest_path}")


if __name__ == "__main__":
    main()
