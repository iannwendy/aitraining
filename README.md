# Vietnamese Depression-Sign Text Classification

Reproducible research pipeline for classifying depression-related textual
signals in Vietnamese YouTube comments. The project covers crawling, cleaning,
weak labeling, blind human review, Round 5 repair, leakage audits, classical and
neural baselines, domain-adaptive pretraining (DAPT), train-only augmentation,
and evaluation on two fixed domains.

The labels are research annotations of text, not clinical diagnoses of authors.
VSMEC is used only as a non-clinical affective transfer proxy.

## Canonical data

| Split/artifact | Rows | Normal | Depression | Role |
|---|---:|---:|---:|---|
| `data/labeled/final_train.csv` | 7,336 | 6,153 | 1,183 | Clean supervised train |
| `data/labeled/final_val.csv` | 241 | 217 | 24 | Fixed human-only model-selection split |
| `data/labeled/final_test.csv` | 242 | 217 | 25 | Fixed human-only in-domain test |
| `data_unified/cross_domain_test.csv` | 3,084 | 1,542 | 1,542 | Fixed VSMEC affective proxy |
| `data/augmented_v2/final_train_augmented.csv` | 10,685 | 6,153 | 4,532 | Train plus accepted synthetic positives |
| `data/translated_en_vi/final_train_translated_en_vi.csv` | 8,628 | 6,799 | 1,829 | Clean train plus balanced translated weak-label pairs |
| `data/translated_en_vi/final_train_augmented_translated_en_vi.csv` | 11,977 | 6,799 | 5,178 | Vietnamese augmentation plus translated weak-label pairs |

The clean train/validation/test total is 7,819 rows. The canonical human-gold
inventory contains 3,915 unique rows including the two holdouts; 3,432 of those
rows occur in train. The remaining 3,904 train rows are high-confidence weak
labels. No external sentiment corpus or VSMEC row is included in supervised
training. The optional translated condition adds 1,292 train-only rows from a
pinned CC0 English Reddit source. Those labels are subreddit/source-derived
weak labels, not expert or clinical annotations; translation provenance remains
visible at row level and its 220-row human audit is still pending.

Machine-readable audits:

- `data/analysis/dataset_integrity_report.json`
- `data/augmented_v2/augmentation_integrity_report.json`
- `data/translated_en_vi/translated_data_integrity_report.json`
- `results/reproducible_round5/reproducibility_manifest.json`

## Evaluated model families

- TF-IDF word/character n-grams with Logistic Regression or LinearSVC.
- Two-layer BiLSTM with random embeddings or frozen PhoBERT embeddings.
- PhoBERT fine-tuning with seeds 42, 123, and 2024.
- Train-only BERTopic features, alone and combined with PhoBERT embeddings.
- Controlled base-PhoBERT versus DAPT-PhoBERT fine-tuning.
- Paired clean-versus-augmented training conditions.
- Optional English-to-Vietnamese auxiliary conditions evaluated as a negative
  result rather than presented as a hidden extension of the native corpus.

The final decision threshold/soft-voting rule is selected on validation only,
locked, and then applied once to the fixed test sets. It is reported separately
from default-threshold model comparisons and is not presented as a new model
architecture.

The translated-data experiment did not improve the fixed holdout. Its locked
ensemble reached validation macro-F1 0.9039 but only 0.7654 on the in-domain
test and 0.3405 on VSMEC. This validation-to-test drop is retained as a negative
result; the test is not reused for threshold tuning.

Canonical results are generated into:

- `results/reproducible_round5/canonical_results.json`
- `results/reproducible_round5/model_comparison.md`
- `results/reproducible_round5/confusion_matrices.json`
- `results/reproducible_round5/statistical_tests.json`
- `results/reproducible_round5/validation_selected_ensemble_results.json`

## Reproduce the study

Use Python 3.9–3.11 and a local PhoBERT base checkpoint at
`models/phobert_base_local/`. The DAPT comparison additionally expects
`models/phobert_domain_adapted/`.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

make dataset
make test
make augment
make translate-en-vi

make classical-clean
make phobert-clean
make phobert-clean-export
make bilstm-clean
make topic-clean
make dapt

make classical-augmented
make phobert-augmented
make bilstm-augmented
make topic-augmented

make classical-translated
make phobert-translated
make classical-augmented-translated
make phobert-augmented-translated

make ensemble-tune
make ensemble-evaluate
make aggregate
make test
```

Detailed protocol, split guarantees, uncertainty estimation, and artifact
descriptions are in [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Integrity guarantees

- Round 5 is repaired from definitive review exports before merging.
- Exact normalized text is unique within each fixed split.
- Train, validation, test, and VSMEC have no exact text overlap.
- Empty text, invalid labels, and missing provenance fail the audit.
- Augmentation occurs after splitting and only modifies train.
- Every synthetic row stores method, seed, and a SHA-256 parent identifier.
- Negation changes, abnormal length changes, duplicates, and holdout overlaps
  are rejected.
- Translated auxiliary rows retain source revision/license/hash, translation
  model revision/license, pair ID, and automatic-audit status.
- Model selection and threshold tuning use validation only; VSMEC is never used
  for fitting, early stopping, or model selection.

## Repository layout

```text
data/labeled/                 canonical supervised splits
data/augmented_v2/            provenance-preserving train augmentation
data/translated_en_vi/        provenance-preserving translated train-only auxiliary data
data_unified/                 cross-domain proxy and broad corpus artifacts
scripts/                      dataset, training, evaluation, and aggregation
tests/                        integrity and regression tests
results/reproducible_round5/  canonical row-level and aggregate results
docs/paper_report.html        manuscript (HTML is the source of truth)
docs/final_fig/prompt.md      corrected figure-generation specifications
web_demo/                     FastAPI/React research demonstration
```

## Web demo

The demo is a research interface, not a diagnostic product.

```bash
# Backend
cd web_demo/backend
uvicorn main:app --reload --port 8000

# Frontend, in a second terminal
cd web_demo
npm run dev
```

The frontend is served at `http://localhost:3000` and the API at
`http://localhost:8000` when using the default development configuration.

## Ethics and intended use

Public accessibility does not imply consent for unrestricted redistribution.
Although account/profile fields are excluded from the research modeling table,
comment text may contain names, locations, contact details, or sensitive
self-disclosure. Raw text therefore requires access control, and quoted examples
should be paraphrased or minimized to reduce search-based re-identification.

Predictions must not be used for diagnosis, surveillance of named individuals,
punitive moderation, employment or insurance decisions, or automated outreach.
Any prospective deployment requires separate ethics review, clinical governance,
human oversight, calibrated uncertainty, and an explicit harm-management plan.
