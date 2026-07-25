"""Build an augmentation-safe training set without touching validation/test.

Only synthetic samples derived from the training set may be appended to train.
Fixed human-only validation/test and VSMEC remain unchanged. Exact overlaps with
any holdout are rejected and recorded in an audit report.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
LABELED_DIR = DATA_DIR / "labeled"
AUGMENTED_DIR = DATA_DIR / "augmented_v2"
GENERATED_FILE = AUGMENTED_DIR / "generated_depression_train.csv"
OUTPUT_TRAIN = AUGMENTED_DIR / "final_train_augmented.csv"
REPORT_FILE = AUGMENTED_DIR / "augmentation_integrity_report.json"
NEGATION_TOKENS = {
    "không", "chẳng", "chả", "chưa", "đừng", "chớ",
    "ko", "k", "khong", "chua", "dung",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


def token_count(value: object) -> int:
    return len(re.findall(r"\w+", normalize_text(value), flags=re.UNICODE))


def negation_signature(value: object) -> tuple[str, ...]:
    tokens = re.findall(r"\w+", normalize_text(value), flags=re.UNICODE)
    return tuple(token for token in tokens if token in NEGATION_TOKENS)


def main() -> dict[str, object]:
    AUGMENTED_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(LABELED_DIR / "final_train.csv")
    val = pd.read_csv(LABELED_DIR / "final_val.csv")
    test = pd.read_csv(LABELED_DIR / "final_test.csv")
    cross = pd.read_csv(PROJECT_DIR / "data_unified" / "cross_domain_test.csv")
    generated_all = pd.read_csv(GENERATED_FILE)
    required_generated = {
        "comment_text", "label", "augmented", "augmentation_method",
        "source_text_sha256", "augmentation_seed",
    }
    missing_generated = required_generated - set(generated_all.columns)
    if missing_generated:
        raise ValueError(f"Generated augmentation file missing: {sorted(missing_generated)}")

    augmented_mask = generated_all["augmented"].astype(str).str.casefold().eq("true")
    originals = generated_all[~augmented_mask].copy()
    originals["label"] = pd.to_numeric(originals["label"], errors="raise").astype(int)
    if originals["source_text_sha256"].duplicated().any():
        raise ValueError("Original augmentation rows contain duplicate source hashes")
    parent_text = originals.set_index("source_text_sha256")["comment_text"].astype(str).to_dict()
    parent_label = originals.set_index("source_text_sha256")["label"].astype(int).to_dict()
    generated = generated_all[augmented_mask].copy()

    generated["label"] = pd.to_numeric(generated["label"], errors="raise").astype(int)
    generated = generated[generated["comment_text"].fillna("").astype(str).str.strip().ne("")].copy()
    generated["_parent_text"] = generated["source_text_sha256"].map(parent_text)
    generated["_parent_label"] = generated["source_text_sha256"].map(parent_label)
    candidate_rows = len(generated)

    missing_parent_mask = generated["_parent_text"].isna()
    removed_missing_parent = int(missing_parent_mask.sum())
    generated = generated[~missing_parent_mask].copy()

    label_mismatch_mask = generated["label"].ne(generated["_parent_label"].astype(int))
    removed_label_mismatch = int(label_mismatch_mask.sum())
    generated = generated[~label_mismatch_mask].copy()

    negation_changed_mask = generated.apply(
        lambda row: negation_signature(row["comment_text"])
        != negation_signature(row["_parent_text"]),
        axis=1,
    )
    removed_negation_change = int(negation_changed_mask.sum())
    generated = generated[~negation_changed_mask].copy()

    parent_lengths = generated["_parent_text"].map(token_count).clip(lower=1)
    length_ratios = generated["comment_text"].map(token_count) / parent_lengths
    length_mask = ~length_ratios.between(0.70, 1.35)
    removed_length_ratio = int(length_mask.sum())
    generated = generated[~length_mask].copy()
    generated["_norm"] = generated["comment_text"].map(normalize_text)

    train_norm = set(train["comment_text"].map(normalize_text))
    holdout_norm = (
        set(val["comment_text"].map(normalize_text))
        | set(test["comment_text"].map(normalize_text))
        | set(cross["comment_text"].map(normalize_text))
    )
    before_overlap = len(generated)
    generated = generated[~generated["_norm"].isin(train_norm | holdout_norm)].copy()
    removed_overlap = before_overlap - len(generated)
    before_dedup = len(generated)
    generated = generated.drop_duplicates("_norm", keep="first")
    removed_duplicates = before_dedup - len(generated)

    synthetic = pd.DataFrame({
        "comment_text": generated["comment_text"].astype(str),
        "label": generated["label"].astype(int),
        "weak_label": "",
        "confidence": "synthetic",
        "depression_score": 0,
        "matched_keywords": "",
        "source": "augmented_train_only",
        "weight": 1,
        "annotation_round": "augmentation_v2",
        "parent_text_sha256": generated["source_text_sha256"].astype(str),
        "augmentation_method": generated["augmentation_method"].astype(str),
        "augmentation_seed": pd.to_numeric(generated["augmentation_seed"], errors="raise").astype(int),
    })
    for column in ["parent_text_sha256", "augmentation_method", "augmentation_seed"]:
        if column not in train.columns:
            train[column] = ""
    output = pd.concat([train, synthetic], ignore_index=True)
    output.to_csv(OUTPUT_TRAIN, index=False, encoding="utf-8-sig")

    output_norm = set(output["comment_text"].map(normalize_text))
    report = {
        "protocol": "augment training only; preserve labels/negation; fixed validation/test/VSMEC untouched",
        "original_train_rows": len(train),
        "generated_candidate_rows": candidate_rows,
        "synthetic_rows_added": len(synthetic),
        "final_augmented_train_rows": len(output),
        "removed_exact_overlap": removed_overlap,
        "removed_duplicate_synthetic_rows": removed_duplicates,
        "quality_filter_rejections": {
            "missing_parent_provenance": removed_missing_parent,
            "label_mismatch_with_parent": removed_label_mismatch,
            "negation_signature_changed": removed_negation_change,
            "token_length_ratio_outside_0.70_to_1.35": removed_length_ratio,
        },
        "unique_source_rows_augmented": int(synthetic["parent_text_sha256"].nunique()),
        "augmentation_methods": {
            str(k): int(v)
            for k, v in synthetic["augmentation_method"].value_counts().sort_index().items()
        },
        "label_distribution": {
            str(int(k)): int(v) for k, v in output["label"].value_counts().sort_index().items()
        },
        "integrity": {
            "null_or_blank_text": int(output["comment_text"].isna().sum() + output["comment_text"].fillna("").astype(str).str.strip().eq("").sum()),
            "duplicate_text": int(output["comment_text"].map(normalize_text).duplicated().sum()),
            "overlap_validation": len(output_norm & set(val["comment_text"].map(normalize_text))),
            "overlap_test": len(output_norm & set(test["comment_text"].map(normalize_text))),
            "overlap_cross_domain": len(output_norm & set(cross["comment_text"].map(normalize_text))),
            "missing_synthetic_parent_hash": int(synthetic["parent_text_sha256"].str.strip().eq("").sum()),
            "missing_synthetic_method": int(synthetic["augmentation_method"].str.strip().eq("").sum()),
            "synthetic_parent_not_in_original_train": int(
                (~synthetic["parent_text_sha256"].isin(set(parent_text))).sum()
            ),
        },
    }
    report["integrity_pass"] = all(value == 0 for value in report["integrity"].values())
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not report["integrity_pass"]:
        raise RuntimeError(f"Augmentation integrity failed; see {REPORT_FILE}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
