import json

import pandas as pd

from scripts import select_validation_ensemble as ensemble


def test_tune_reads_validation_scores_only(tmp_path, monkeypatch):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    lock_file = results_dir / "lock.json"
    monkeypatch.setattr(ensemble, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(ensemble, "LOCK_FILE", lock_file)

    pd.DataFrame({
        "comment_text": ["a", "b", "c", "d"],
        "label": [0, 0, 1, 1],
        "prediction": [0, 0, 1, 1],
        "score_depression": [0.1, 0.2, 0.8, 0.9],
    }).to_csv(results_dir / "tfidf_logreg_clean_validation_predictions.csv", index=False)

    # If tune accidentally touches the test split, this malformed file would fail.
    (results_dir / "tfidf_logreg_clean_in_domain_predictions.csv").write_text(
        "this,is,not,the,expected,schema\n", encoding="utf-8"
    )

    result = ensemble.tune()

    assert result["winner"]["metrics"]["f1_macro"] == 1.0
    assert result["required_sources"] == ["tfidf_logreg_clean"]
    assert json.loads(lock_file.read_text(encoding="utf-8"))["protocol"].startswith(
        "Model/weight/threshold selected using final_val.csv only"
    )


def test_all_candidate_component_weights_sum_to_one():
    names = [
        "tfidf_logreg_clean",
        "tfidf_linearsvc_clean",
        "phobert_clean_seed42",
        "phobert_clean_seed123",
        "phobert_clean_seed2024",
    ]
    candidates = ensemble.candidate_definitions(names)
    assert candidates
    for candidate in candidates:
        assert abs(sum(candidate["components"].values()) - 1.0) < 1e-12


def test_translated_training_tags_form_condition_specific_candidates():
    names = [
        "tfidf_logreg_translated",
        "tfidf_linearsvc_translated",
        "phobert_translated_seed42",
        "phobert_translated_seed123",
        "tfidf_logreg_augmented_translated",
        "tfidf_linearsvc_augmented_translated",
    ]
    candidates = ensemble.candidate_definitions(names)
    by_name = {candidate["name"]: candidate for candidate in candidates}

    assert "tfidf_translated_soft_vote" in by_name
    assert "translated_phobert0.50_tfidf0.50" in by_name
    assert "tfidf_augmented_translated_soft_vote" in by_name
