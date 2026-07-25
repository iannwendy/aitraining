# Reproducing the repaired Round-5 study

This document is the canonical execution guide for the results reported in
`docs/paper_report.html`. Historical files under `results/round*`, old
`models/*round5*` artifacts without a `clean`/`augmented` tag, and scripts under
`docs/scripts/` are not inputs to the final tables.

## 1. Environment

Use Python 3.9–3.11 in a fresh virtual environment. The completed run recorded
its exact platform, package versions, dataset hashes, and result hashes in
`results/reproducible_round5/reproducibility_manifest.json`.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

PhoBERT experiments require the local base checkpoint at
`models/phobert_base_local/`. The DAPT comparison additionally requires the
continued-MLM checkpoint at `models/phobert_domain_adapted/`. Training supports
CUDA, Apple MPS, and CPU, although CPU runs are substantially slower. Small
floating-point differences can occur across accelerators; stochastic models
therefore use seeds 42, 123, and 2024 and are reported as mean ± sample standard
deviation.

## 2. Rebuild and audit the data

```bash
PYTHONPATH="$PWD" .venv/bin/python scripts/merge_round5_reviewed.py
.venv/bin/python -m pytest -q
```

Expected canonical split sizes:

| Split | Rows | Normal | Depression | Policy |
|---|---:|---:|---:|---|
| Train | 7,336 | 6,153 | 1,183 | pre-R5 gold + valid R5 labels + high-confidence weak labels |
| Validation | 241 | 217 | 24 | fixed human-only holdout |
| In-domain test | 242 | 217 | 25 | fixed human-only holdout |
| VSMEC proxy | 3,084 | 1,542 | 1,542 | fixed affective cross-domain proxy; never trained on |

The machine-readable audit is
`data/analysis/dataset_integrity_report.json`. A valid rebuild has no blank
text, invalid labels, within-split duplicates, train/validation/test overlap,
or exact overlap with VSMEC.

## 3. Rebuild the train-only augmentation

```bash
TQDM_DISABLE=1 PYTHONPATH="$PWD" .venv/bin/python scripts/data_augmentation.py \
  --input data/labeled/final_train.csv \
  --output data/augmented_v2/generated_depression_train.csv \
  --depression-only --n-augment 3

PYTHONPATH="$PWD" .venv/bin/python scripts/merge_augmented.py
.venv/bin/python -m pytest -q
```

The split is made before augmentation and is never recomputed afterward.
Synthetic rows are appended only to train. Each row stores its transformation,
seed, and SHA-256 parent-text identifier. The merger rejects missing parent
provenance, label changes, changed negation signatures, abnormal token-length
ratios, duplicates, and holdout overlaps. See
`data/augmented_v2/augmentation_integrity_report.json` for the exact final
count and rejection reasons.

## 4. Build and evaluate the optional translated auxiliary condition

Before training the main comparison, the optional translated auxiliary set can
be rebuilt with:

```bash
make translate-en-vi
```

The source is `hugginglearners/reddit-depression-cleaned` at revision
`c71fde85d3a85330916731069ebbb3461816404b` (CC0-1.0; file SHA-256
`bc5fc11e77b4388c6484f580824900484c2b58f8ed4dce32c6d1cb78c48ed7e9`).
Its binary labels are subreddit/source-derived weak labels rather than expert
diagnoses. The script length-matches 1,100 depression/normal pairs, translates
locally with `facebook/nllb-200-distilled-600M` revision
`f8d333a098d19b4fd9a8b18f94170487ad3f821d` (CC-BY-NC-4.0), and applies
complete-pair gates for PII patterns, negation preservation, length ratio,
cross-lingual cosine, duplicates, label conflict, and exact split overlap.

In the recorded run, 646 complete pairs (1,292 rows; 646 per label) passed.
No accepted row overlapped train, validation, test, or VSMEC. Row-level source
and translation provenance are retained in the merged train files. The exported
220-row human translation audit remains pending and must not be described as
completed.

Translated candidate training is validation-only:

```bash
make classical-translated
make phobert-translated
make classical-augmented-translated
make phobert-augmented-translated
```

These commands do not load either final holdout. After the winner was locked,
only its required component checkpoints were exported to the two holdouts.
The locked five-component ensemble achieved validation macro-F1 0.9039 but
in-domain macro-F1 0.7654 and VSMEC macro-F1 0.3405. This is a negative result:
the small 24-positive validation set did not provide a stable threshold for the
25-positive test set. The existing holdout result must not be deleted and the
same test must not be reused to select another threshold or winner.

The detailed record is
`results/reproducible_round5/translated_auxiliary_experiment.md`.

## 5. Train and evaluate the clean models

```bash
make classical-clean
make phobert-clean
make phobert-clean-export
make bilstm-clean
make topic-clean
make dapt
```

All supervised estimators fit only the training split. Validation is used for
checkpoint selection where applicable. Both final domains are evaluated with
the same six metrics: accuracy, macro precision, macro recall, macro F1,
weighted F1, and depression-class F1. Confusion matrices always use label order
`[normal=0, depression=1]` for both rows and columns.

The BERTopic classifier is fitted from scratch on the supervised training text
only. The historical 316K-corpus BERTopic object is descriptive and must not be
used for predictive evaluation because that corpus contains holdout text.

The DAPT task is a controlled encoder comparison: both the base and
domain-adapted checkpoints are fine-tuned using the same data, sample weighting,
hyperparameters, seeds, and evaluation code. These rows should be interpreted
within the DAPT experiment rather than mixed with the main-model ranking.

## 6. Train and evaluate the augmented models

```bash
make classical-augmented
make phobert-augmented
make bilstm-augmented
make topic-augmented
```

Validation, in-domain test, and VSMEC files are byte-identical between clean
and augmented runs. This makes each clean-versus-augmented comparison paired at
the row level.

## 7. Lock the final threshold/ensemble without test tuning

```bash
make ensemble-tune
make ensemble-evaluate
```

`ensemble-tune` reads only row-level scores for `final_val.csv`. It compares a
predefined set of individual models and soft-voting combinations, selects the
highest validation macro-F1, and stores the locked components, weights,
threshold, and input hashes in
`results/reproducible_round5/validation_selected_ensemble.json`. The tune phase
does not load either test file.

`ensemble-evaluate` then applies that locked configuration once to the fixed
in-domain test and VSMEC proxy. It refuses to overwrite an existing final
holdout result, which prevents casual test-driven retuning. Threshold selection
on a 241-row validation set is reported explicitly and is not presented as a
new model architecture.

## 8. Freeze tables and statistical outputs

```bash
make aggregate
```

This produces:

- `results/reproducible_round5/canonical_results.json`
- `results/reproducible_round5/model_comparison.md`
- `results/reproducible_round5/confusion_matrices.json`
- `results/reproducible_round5/statistical_tests.json`
- `results/reproducible_round5/reproducibility_manifest.json`

Macro-F1 uncertainty uses a stratified percentile bootstrap with 2,000
resamples and seed 42. Clean-versus-augmented point predictions use paired
bootstrap differences and exact McNemar tests with Holm correction within each
evaluation domain. Multi-seed mean/std, majority-vote point estimates, and
single reference-seed confusion matrices are kept explicitly separate.

## 9. Manuscript and figures

Only synchronize final numbers from the canonical result files into
`docs/paper_report.html`. VSMEC must be described as a non-clinical affective
proxy (Sadness/Fear versus Enjoyment), not as depression ground truth. Image
generation is intentionally outside the reproducible code path; the corrected
specifications live in `docs/final_fig/prompt.md`.
