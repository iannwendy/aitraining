"""Regression tests for the train-only English-to-Vietnamese auxiliary data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from scripts import build_translated_english_train as translated


def test_length_matched_selection_is_balanced_and_traceable():
    rows = []
    for label in (0, 1):
        for index in range(8):
            rows.append({
                "clean_text": f"label {label} example {index} " + "word " * (8 + index),
                "is_depression": label,
            })
    rows.extend([
        {"clean_text": "contact me test@example.com " + "word " * 8, "is_depression": 0},
        {"clean_text": "label 0 example 0 " + "word " * 8, "is_depression": 0},
        {"clean_text": "same conflicting text " + "word " * 8, "is_depression": 0},
        {"clean_text": "same conflicting text " + "word " * 8, "is_depression": 1},
    ])

    selected, report = translated.select_length_matched_pairs(
        pd.DataFrame(rows), per_class=4, seed=7, max_source_chars=144
    )

    assert len(selected) == 8
    assert selected["label"].value_counts().to_dict() == {0: 4, 1: 4}
    assert selected.groupby("pair_id")["label"].nunique().eq(2).all()
    assert selected["source_text_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert report["available_length_matched_pairs"] >= report["selected_pairs"]
    assert report["rejected"]["pii_pattern"] == 1
    assert report["rejected"]["source_label_conflict_rows"] == 2


def test_translation_audit_accepts_only_complete_passing_pairs(monkeypatch):
    class FakeSimilarityModel:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, **kwargs):
            return np.tile(np.array([[1.0, 0.0]]), (len(texts), 1))

    monkeypatch.setattr(translated, "SentenceTransformer", FakeSimilarityModel)
    monkeypatch.setattr(
        translated,
        "load_holdout_keys",
        lambda: {name: set() for name in ("train", "validation", "test", "cross_domain")},
    )
    frame = pd.DataFrame({
        "pair_id": ["pair_ok", "pair_ok", "pair_bad", "pair_bad"],
        "source_text_en": [
            "I feel calm today",
            "I feel very sad today",
            "I am not sad today",
            "I feel fine today",
        ],
        "comment_text": [
            "Hôm nay tôi thấy bình tĩnh",
            "Hôm nay tôi thấy rất buồn",
            "Hôm nay tôi thấy buồn",
            "Hôm nay tôi thấy ổn",
        ],
        "label": [0, 1, 1, 0],
    })

    accepted, report = translated.audit_translations(
        frame, similarity_threshold=0.45, seed=7
    )

    assert set(accepted["pair_id"]) == {"pair_ok"}
    assert len(accepted) == 2
    assert report["accepted_complete_pairs"] == 1
    assert report["automatic_rejections_by_reason"]["negation_mismatch"] == 1
    assert accepted["translation_audit_status"].eq(
        "automatic_pass_human_audit_pending"
    ).all()
