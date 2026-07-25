"""Regression checks for the repaired Round-5 dataset protocol."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
LABELED_DIR = PROJECT_DIR / "data" / "labeled"


def norm(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(LABELED_DIR / name)


def test_integrity_report_passes():
    report = json.loads((PROJECT_DIR / "data" / "analysis" / "dataset_integrity_report.json").read_text())
    assert report["integrity_pass"] is True


def test_splits_have_valid_schema_and_no_blank_text():
    required = {"comment_text", "label", "source", "weight", "annotation_round"}
    for name in ["final_train.csv", "final_val.csv", "final_test.csv"]:
        frame = load(name)
        assert required <= set(frame.columns)
        assert frame["comment_text"].notna().all()
        assert frame["comment_text"].astype(str).str.strip().ne("").all()
        assert set(frame["label"].astype(int).unique()) <= {0, 1}


def test_no_duplicate_or_cross_split_overlap():
    train = {norm(x) for x in load("final_train.csv")["comment_text"]}
    val = {norm(x) for x in load("final_val.csv")["comment_text"]}
    test = {norm(x) for x in load("final_test.csv")["comment_text"]}
    cross = {
        norm(x)
        for x in pd.read_csv(PROJECT_DIR / "data_unified" / "cross_domain_test.csv")["comment_text"]
    }
    assert len(train) == len(load("final_train.csv"))
    assert len(val) == len(load("final_val.csv"))
    assert len(test) == len(load("final_test.csv"))
    assert not train & val
    assert not train & test
    assert not val & test
    assert not train & cross
    assert not val & cross
    assert not test & cross


def test_validation_and_test_are_human_only():
    for name in ["final_val.csv", "final_test.csv"]:
        frame = load(name)
        assert frame["source"].astype(str).str.startswith("human_gold_fixed_").all()


def test_round5_is_unique_and_train_only():
    round5 = pd.read_csv(PROJECT_DIR / "data" / "round5" / "round5_reviewed_clean.csv")
    assert len(round5) == 1360
    assert round5["comment_text"].map(norm).nunique() == 1360
    train = load("final_train.csv")
    assert (train["source"] == "human_gold_round5").sum() == 1360
    assert not load("final_val.csv")["source"].eq("human_gold_round5").any()
    assert not load("final_test.csv")["source"].eq("human_gold_round5").any()


def test_augmentation_is_train_only_and_traceable():
    report_path = PROJECT_DIR / "data" / "augmented_v2" / "augmentation_integrity_report.json"
    augmented_path = PROJECT_DIR / "data" / "augmented_v2" / "final_train_augmented.csv"
    if not report_path.exists() or not augmented_path.exists():
        return

    report = json.loads(report_path.read_text(encoding="utf-8"))
    augmented = pd.read_csv(augmented_path, dtype=str).fillna("")
    synthetic = augmented[augmented["source"].eq("augmented_train_only")]
    assert report["integrity_pass"] is True
    assert len(augmented) == report["final_augmented_train_rows"]
    assert len(synthetic) == report["synthetic_rows_added"]
    assert synthetic["parent_text_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert synthetic["augmentation_method"].str.strip().ne("").all()
    assert synthetic["augmentation_seed"].eq("42").all()


def test_translated_auxiliary_data_is_train_only_balanced_and_traceable():
    translated_dir = PROJECT_DIR / "data" / "translated_en_vi"
    report_path = translated_dir / "translated_data_integrity_report.json"
    accepted_path = translated_dir / "translated_vi_accepted.csv"
    merged_path = translated_dir / "final_train_translated_en_vi.csv"
    if not report_path.exists() or not accepted_path.exists() or not merged_path.exists():
        return

    report = json.loads(report_path.read_text(encoding="utf-8"))
    accepted = pd.read_csv(accepted_path, dtype=str).fillna("")
    merged = pd.read_csv(merged_path, dtype=str).fillna("")
    auxiliary = merged[merged["source"].eq("translated_en_reddit_cc0")]

    assert report["integrity_pass"] is True
    assert len(accepted) == report["quality_audit"]["accepted_rows"]
    assert accepted["label"].value_counts().to_dict() == {"0": 646, "1": 646}
    assert len(auxiliary) == len(accepted)
    assert auxiliary["source_text_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert auxiliary["source_revision"].eq(report["source"]["revision"]).all()
    assert auxiliary["translation_model_revision"].eq(
        report["translation"]["revision"]
    ).all()
    assert auxiliary["translation_audit_status"].eq(
        "automatic_pass_human_audit_pending"
    ).all()
