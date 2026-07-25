## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-25
- Verification Status: ANALYZED
- Version Label: translated_auxiliary_exp_v1

## Experiment Result

- **ID**: translated_en_vi_round5_20260725
- **Type**: ETL + machine translation + model training + locked evaluation
- **Status**: completed
- **Working Directory**: `/Users/iannwendy/Documents/crawl_yt/youtube_depression_crawler`
- **Selection Policy**: train only; model/weights/threshold selected on `final_val.csv`; fixed test and VSMEC loaded once after locking

### Source and translation

| Item | Fixed value |
|---|---|
| English source | `hugginglearners/reddit-depression-cleaned` |
| Source revision | `c71fde85d3a85330916731069ebbb3461816404b` |
| Source license | CC0-1.0 |
| Source file SHA-256 | `bc5fc11e77b4388c6484f580824900484c2b58f8ed4dce32c6d1cb78c48ed7e9` |
| Label provenance | Subreddit/source-derived weak labels; not expert or clinical diagnoses |
| Translation model | `facebook/nllb-200-distilled-600M` |
| Translation revision | `f8d333a098d19b4fd9a8b18f94170487ad3f821d` |
| Translation-model license | CC-BY-NC-4.0 |
| Similarity model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Similarity revision | `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` |

The source contained 7,731 rows. Selection produced 1,100 balanced,
source-length-matched pairs (2,200 rows). Automatic complete-pair gates accepted
646 pairs (1,292 rows; 646 per class). No accepted translation had an exact
overlap with train, validation, in-domain test, or VSMEC. The exported 220-row
human translation audit remains pending.

### Commands

```bash
.venv/bin/python scripts/build_translated_english_train.py
.venv/bin/python scripts/train_evaluate_classical.py --train-file data/translated_en_vi/final_train_translated_en_vi.csv --tag translated --splits validation
.venv/bin/python scripts/train_evaluate_classical.py --train-file data/translated_en_vi/final_train_augmented_translated_en_vi.csv --tag augmented_translated --splits validation
.venv/bin/python scripts/train_phobert_round5_multiseed.py --train-file data/translated_en_vi/final_train_translated_en_vi.csv --seeds 42 123 2024 --result-name phobert_results_translated.json --output-dir models/round5_predictions_translated --evaluation-splits validation
.venv/bin/python scripts/train_phobert_round5_multiseed.py --train-file data/translated_en_vi/final_train_augmented_translated_en_vi.csv --seeds 42 123 2024 --result-name phobert_results_augmented_translated.json --output-dir models/round5_predictions_augmented_translated --evaluation-splits validation
.venv/bin/python scripts/select_validation_ensemble.py tune
.venv/bin/python scripts/train_evaluate_classical.py --train-file data/translated_en_vi/final_train_augmented_translated_en_vi.csv --tag augmented_translated --splits in_domain cross_domain --result-name classical_results_augmented_translated_holdout.json
.venv/bin/python scripts/export_phobert_predictions.py --model-root models/round5_predictions_augmented_translated --tag augmented_translated --seeds 42 123 2024 --splits in_domain cross_domain
.venv/bin/python scripts/select_validation_ensemble.py evaluate
```

### Main results

| Model/condition | Validation macro-F1 | In-domain macro-F1 | VSMEC macro-F1 |
|---|---:|---:|---:|
| TF-IDF Logistic Regression, augmented + translated | 0.8182 | 0.7956 | 0.3839 |
| TF-IDF LinearSVC, augmented + translated | 0.8438 | 0.7770 | 0.3743 |
| PhoBERT, augmented + translated, 3-seed mean ± SD | 0.8721 ± 0.0233 | 0.7761 ± 0.0080 | 0.3555 ± 0.0020 |
| Locked 25% PhoBERT / 75% TF-IDF soft vote | **0.9039** | **0.7654** | **0.3405** |

Locked validation confusion: `[[214, 3], [5, 19]]`.

One-time in-domain confusion: `[[212, 5], [13, 12]]`.

One-time VSMEC confusion: `[[1542, 0], [1532, 10]]`.

The in-domain fixed-prediction bootstrap macro-F1 95% percentile interval was
0.6585–0.8541 (10,000 resamples, seed 20260725). Positive-score median shifted
from 0.8473 on validation to 0.5767 on the in-domain test at the locked threshold
0.63.

### Output files

| Artifact | Purpose |
|---|---|
| `data/translated_en_vi/translated_data_integrity_report.json` | Source, selection, translation and overlap audit |
| `data/translated_en_vi/final_train_translated_en_vi.csv` | Clean + translated train condition |
| `data/translated_en_vi/final_train_augmented_translated_en_vi.csv` | Vietnamese augmentation + translated train condition |
| `results/reproducible_round5/phobert_results_translated.json` | Validation-only three-seed PhoBERT run |
| `results/reproducible_round5/phobert_results_augmented_translated.json` | Validation-only three-seed PhoBERT run |
| `results/reproducible_round5/validation_selected_ensemble.json` | Locked validation selection with source hashes |
| `results/reproducible_round5/validation_selected_ensemble_results.json` | One-time fixed-holdout result |

### Anomalies and interpretation

- Translation completed without crash. Training produced long log-silent
  intervals because metrics are emitted only at epoch boundaries; process and
  resource checks confirmed continued execution.
- Validation performance did not transfer to the fixed test. The 24-positive
  validation split was too small to support stable threshold/ensemble selection
  across the expanded candidate set.
- The translated source has weak subreddit-derived labels and a source-domain
  length confound. Length matching and clipping mitigate but do not remove its
  construct mismatch with Vietnamese YouTube annotations.
- Human review of translation fidelity is not complete. The translated condition
  therefore remains auxiliary and should not be promoted to the canonical model.
- The fixed test must not be reused to choose a lower threshold or a different
  winner. Further confirmatory improvement requires a new independently annotated
  validation/test sample or a predeclared nested cross-validation design.
