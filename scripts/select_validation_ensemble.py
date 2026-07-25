"""Select a threshold/soft-voting ensemble on validation, then lock and test it.

The ``tune`` phase reads validation prediction files only. The ``evaluate``
phase consumes the locked JSON configuration and evaluates the untouched fixed
in-domain and VSMEC holdouts. Keeping the phases separate makes accidental
test-driven threshold selection harder and leaves an auditable selection trail.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results" / "reproducible_round5"
LOCK_FILE = RESULTS_DIR / "validation_selected_ensemble.json"
FINAL_FILE = RESULTS_DIR / "validation_selected_ensemble_results.json"
THRESHOLDS = np.round(np.arange(0.05, 0.951, 0.01), 2)
BLEND_WEIGHTS = (0.25, 0.5, 0.75)
TRAINING_TAGS = ("clean", "augmented", "translated", "augmented_translated")


@dataclass(frozen=True)
class ScoreSource:
    name: str
    path: Path
    scores: np.ndarray


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def score_column(frame: pd.DataFrame) -> str:
    for column in ("probability_depression", "score_depression"):
        if column in frame.columns:
            return column
    raise ValueError("Prediction file lacks probability_depression/score_depression")


def source_name(path: Path, split: str) -> str:
    suffix = f"_{split}_predictions.csv"
    if not path.name.endswith(suffix):
        raise ValueError(f"Unexpected prediction filename: {path.name}")
    return path.name.removesuffix(suffix)


def load_sources(split: str, required: list[str] | None = None) -> tuple[pd.DataFrame, dict[str, ScoreSource]]:
    paths = sorted(RESULTS_DIR.glob(f"*_{split}_predictions.csv"))
    if required is not None:
        wanted = set(required)
        paths = [path for path in paths if source_name(path, split) in wanted]
        missing = wanted - {source_name(path, split) for path in paths}
        if missing:
            raise FileNotFoundError(f"Missing {split} score files for: {sorted(missing)}")
    if not paths:
        raise FileNotFoundError(f"No {split} prediction files found in {RESULTS_DIR}")

    reference: pd.DataFrame | None = None
    sources: dict[str, ScoreSource] = {}
    for path in paths:
        frame = pd.read_csv(path)
        if not {"comment_text", "label"}.issubset(frame.columns):
            continue
        try:
            column = score_column(frame)
        except ValueError:
            continue
        aligned = frame[["comment_text", "label"]].copy()
        aligned["comment_text"] = aligned["comment_text"].astype(str)
        aligned["label"] = aligned["label"].astype(int)
        if reference is None:
            reference = aligned
        elif not reference.equals(aligned):
            raise ValueError(f"Row order/content mismatch: {path}")
        name = source_name(path, split)
        scores = frame[column].astype(float).to_numpy()
        if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
            raise ValueError(f"Scores outside [0, 1] or non-finite: {path}")
        sources[name] = ScoreSource(name=name, path=path, scores=scores)
    if reference is None or not sources:
        raise ValueError(f"No usable score-bearing {split} prediction files")
    return reference, sources


def metric_dict(labels: np.ndarray, predictions: np.ndarray) -> dict[str, object]:
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision_macro": float(
            precision_score(labels, predictions, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(labels, predictions, average="macro", zero_division=0)
        ),
        "f1_macro": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "f1_weighted": float(
            f1_score(labels, predictions, average="weighted", zero_division=0)
        ),
        "f1_depression": float(
            f1_score(labels, predictions, average="binary", pos_label=1, zero_division=0)
        ),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def candidate_definitions(names: list[str]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = [
        {"name": name, "components": {name: 1.0}, "complexity": 1}
        for name in names
    ]

    def add_average(label: str, members: list[str]) -> str | None:
        members = sorted(set(member for member in members if member in names))
        if len(members) < 2:
            return None
        weight = 1.0 / len(members)
        candidates.append({
            "name": label,
            "components": {member: weight for member in members},
            "complexity": len(members),
        })
        return label

    virtual: dict[str, dict[str, float]] = {}
    for tag in TRAINING_TAGS:
        phobert = sorted(name for name in names if re.fullmatch(fr"phobert_{tag}_seed\d+", name))
        tfidf = sorted(name for name in names if name in {
            f"tfidf_logreg_{tag}", f"tfidf_linearsvc_{tag}"
        })
        phobert_label = add_average(f"phobert_{tag}_soft_vote", phobert)
        tfidf_label = add_average(f"tfidf_{tag}_soft_vote", tfidf)
        if phobert_label:
            virtual[phobert_label] = next(
                candidate["components"] for candidate in candidates if candidate["name"] == phobert_label
            )
        if tfidf_label:
            virtual[tfidf_label] = next(
                candidate["components"] for candidate in candidates if candidate["name"] == tfidf_label
            )
        if phobert_label and tfidf_label:
            for weight in BLEND_WEIGHTS:
                components: dict[str, float] = {}
                for member, member_weight in virtual[phobert_label].items():
                    components[member] = components.get(member, 0.0) + weight * member_weight
                for member, member_weight in virtual[tfidf_label].items():
                    components[member] = components.get(member, 0.0) + (1 - weight) * member_weight
                candidates.append({
                    "name": f"{tag}_phobert{weight:.2f}_tfidf{1-weight:.2f}",
                    "components": components,
                    "complexity": len(components),
                })

    add_average(
        "tfidf_logreg_clean_augmented_soft_vote",
        ["tfidf_logreg_clean", "tfidf_logreg_augmented"],
    )
    add_average(
        "tfidf_all_soft_vote",
        [name for name in names if name.startswith("tfidf_")],
    )
    all_phobert = [
        name
        for name in names
        if any(re.fullmatch(fr"phobert_{tag}_seed\d+", name) for tag in TRAINING_TAGS)
    ]
    add_average("phobert_all_training_conditions_soft_vote", all_phobert)
    return candidates


def combine(components: dict[str, float], sources: dict[str, ScoreSource]) -> np.ndarray:
    total = sum(float(weight) for weight in components.values())
    if not np.isclose(total, 1.0):
        raise ValueError(f"Component weights must sum to 1, got {total}")
    return sum(float(weight) * sources[name].scores for name, weight in components.items())


def tune() -> dict[str, object]:
    reference, sources = load_sources("validation")
    labels = reference["label"].to_numpy()
    rows: list[dict[str, object]] = []
    for candidate in candidate_definitions(sorted(sources)):
        scores = combine(candidate["components"], sources)
        for threshold in THRESHOLDS:
            predictions = (scores >= threshold).astype(int)
            metrics = metric_dict(labels, predictions)
            rows.append({
                "name": candidate["name"],
                "components": candidate["components"],
                "complexity": candidate["complexity"],
                "threshold": float(threshold),
                "metrics": metrics,
            })
    rows.sort(key=lambda row: (
        -float(row["metrics"]["f1_macro"]),
        int(row["complexity"]),
        abs(float(row["threshold"]) - 0.5),
        str(row["name"]),
    ))
    winner = rows[0]
    required = sorted(winner["components"])
    lock = {
        "protocol": (
            "Model/weight/threshold selected using final_val.csv only; fixed in-domain "
            "test and VSMEC files were not loaded by the tune phase"
        ),
        "selection_objective": "maximum validation macro-F1",
        "threshold_grid": [float(THRESHOLDS[0]), float(THRESHOLDS[-1]), 0.01],
        "blend_weights": list(BLEND_WEIGHTS),
        "validation_rows": int(len(reference)),
        "validation_positive_rows": int(labels.sum()),
        "winner": winner,
        "required_sources": required,
        "source_sha256": {name: sha256(sources[name].path) for name in required},
        "top_10": rows[:10],
    }
    LOCK_FILE.write_text(json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Locked {winner['name']} at threshold={winner['threshold']:.2f}; "
        f"validation macro-F1={winner['metrics']['f1_macro']:.4f}"
    )
    print(f"Saved: {LOCK_FILE}")
    return lock


def evaluate() -> dict[str, object]:
    if not LOCK_FILE.exists():
        raise FileNotFoundError(f"Tune first; missing {LOCK_FILE}")
    if FINAL_FILE.exists():
        raise FileExistsError(
            f"Refusing to overwrite one-time holdout evaluation: {FINAL_FILE}"
        )
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    winner = lock["winner"]
    required = list(lock["required_sources"])
    threshold = float(winner["threshold"])
    report: dict[str, object] = {
        "protocol": "locked validation-selected configuration; evaluated once on fixed holdouts",
        "selection": winner,
        "splits": {},
    }
    for split in ("in_domain", "cross_domain"):
        reference, sources = load_sources(split, required=required)
        scores = combine(winner["components"], sources)
        predictions = (scores >= threshold).astype(int)
        labels = reference["label"].to_numpy()
        report["splits"][split] = metric_dict(labels, predictions)
        pd.DataFrame({
            "comment_text": reference["comment_text"],
            "label": labels,
            "prediction": predictions,
            "score_depression": scores,
            "locked_threshold": threshold,
        }).to_csv(RESULTS_DIR / f"validation_selected_ensemble_{split}_predictions.csv", index=False)
    FINAL_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    in_domain = report["splits"]["in_domain"]
    print(
        f"Final in-domain macro-F1={in_domain['f1_macro']:.4f}; "
        f"confusion={in_domain['confusion_matrix']}"
    )
    print(f"Saved: {FINAL_FILE}")
    return report


def main() -> dict[str, object]:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("tune", "evaluate"))
    args = parser.parse_args()
    return tune() if args.phase == "tune" else evaluate()


if __name__ == "__main__":
    main()
