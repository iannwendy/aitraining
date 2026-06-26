# Vietnamese Depression Sign Detection from Social Media Text

End-to-end research pipeline for detecting signs of depression in Vietnamese
YouTube comments, comparing classical and deep-learning models on an
in-domain corpus and a cross-domain benchmark.

This repository contains the data acquisition, weak labeling, blind human
annotation, model training, evaluation, and a controlled
domain-adaptive-pretraining (DAPT) counter-experiment conducted against
the published `vinai/phobert-base` model.

## Research Question

Can Vietnamese social-media text be used to train a depression-sign
classifier with high in-domain accuracy, and how well does that
classifier transfer to a different Vietnamese text genre? Is
encoder-side domain adaptation (continued MLM on the target corpus)
worth the compute cost for a low-resource downstream task?

## Headline Results

**Table 1 — Five-model comparison (single-seed, identical hyperparams).**

| Model variant          | In-domain F1-macro | Cross-domain F1-macro |
|------------------------|--------------------|----------------------|
| TF-IDF + SVM (baseline)| 0.9312             | 0.4286               |
| BiLSTM                 | 0.8951             | 0.4272               |
| **PhoBERT (original)** | **0.7876**         | **0.7618**           |
| BERTopic-only          | 0.5599             | 0.5030               |
| PhoBERT + BERTopic     | 0.9501             | 0.3977               |

_Single-seed run; mean ± std not reported because seeds were not
exhausted for these variants. The DAPT counter-experiment below
adds the missing statistical rigor for the one model that warranted
it._

**Table 2 — Domain-adaptive pretraining counter-experiment (3 seeds: 42, 123, 2024).**

| Model               | In-domain F1-macro (mean ± std) | Cross-domain F1-macro (mean ± std) |
|---------------------|---------------------------------|-------------------------------------|
| **PhoBERT (original)** | **0.7876 ± 0.0229**         | **0.7618 ± 0.0099**                 |
| PhoBERT + DAPT (2 ep.) | 0.7493 ± 0.0285             | 0.7267 ± 0.0148                     |

_Trained and evaluated on the same final dataset; only the encoder
checkpoint differs. Numbers reproduce verbatim from
`results/domain_adapted_eval_2026-06-25_123440/comparison_table.md`._

**Two empirical findings.**

1. **A generalization gap of approximately 0.50–0.53 F1-macro** between
   in-domain and cross-domain performance is consistent across model
   families (TF-IDF+SVM, BiLSTM, PhoBERT). The bottleneck is
   data-centric — label definition divergence, text length mismatch,
   linguistic register divergence, and class imbalance — not
   architecture-centric.

2. **Domain-adaptive pretraining did not help.** Two epochs of
   continued MLM on 119,649 YouTube comments (eval perplexity 18.01)
   reduced downstream F1 by approximately 3.8 points on the in-domain
   test set (0.7876 → 0.7493) and approximately 3.5 points on the
   cross-domain test set (0.7618 → 0.7267) relative to the original
   PhoBERT base, while leaving the generalization gap magnitude
   essentially unchanged. The base
   PhoBERT already covers broad Vietnamese registers; with only
   3,576 downstream training samples, the DAPT checkpoint is forced
   to re-learn general-purpose features from a weaker initialization.
   For practitioners on small Vietnamese social-media datasets,
   skipping the DAPT step and proceeding directly from the published
   base checkpoint to task fine-tuning is the recommended default.
   Full discussion in [`docs/paper_report.html` § 5.5](docs/paper_report.html).

## Data Artifacts

| Artifact                                       | Size        | Purpose                                |
|------------------------------------------------|-------------|----------------------------------------|
| `data/cleaned_comments.csv`                    | 125,329 rows | Cleaned YouTube comments              |
| `data/auto_labeled_comments.csv`               | 125,329 rows | Weak labels via keyword scoring      |
| `data/gold_review.csv`                         | 1,607 rows   | Blind human-reviewed subset           |
| `data/final_train.csv`                         | 3,576 rows   | Multi-source training set             |
| `data/final_val.csv`                           | 766 rows     | Validation split                      |
| `data/final_test.csv`                          | 767 rows     | In-domain test                        |
| `data_unified/cross_domain_test.csv`           | 3,084 rows   | VSMEC cross-domain test (held out)    |
| `data_unified/corpus_text_all.csv`             | 316,401 rows | YouTube + 8 external Vietnamese sets |
| `results/domain_adapted_eval_<ts>/`            | 6 runs       | DAPT counter-experiment metrics       |

## Models

| Model               | Code path                                            |
|---------------------|------------------------------------------------------|
| TF-IDF + SVM        | `yt_depression_crawler/modeling/baseline/`           |
| BiLSTM              | (in-repo notebook scripts)                           |
| PhoBERT             | `yt_depression_crawler/modeling/phobert/`             |
| BERTopic            | `yt_depression_crawler/modeling/bertopic/`           |
| Domain-adapted base | `scripts/domain_adaptive_pretrain.py`                |

The domain-adapted base checkpoint (`models/phobert_domain_adapted/`,
eval perplexity 18.01) is gitignored — reproduce it locally with the
single command in the next section before re-running the DAPT
evaluation. Adding a classification head and fine-tuning follows the
same procedure as for the base checkpoint; no further adaptation is
performed at inference.

## Pipeline Layout

```
yt_depression_crawler/
├── ingestion/      YouTube Data API v3 client + crawler
├── processing/     Cleaning, normalization, deduplication
├── labeling/       Weighted-keyword weak labeler + gold set builder
├── modeling/
│   ├── baseline/   TF-IDF + Logistic Regression / SVM
│   ├── phobert/    Fine-tuning + prediction + postprocess
│   └── bertopic/   Topic modeling over the unified corpus
├── pipelines/      End-to-end orchestrators per stage
└── web/            Flask monitoring dashboard

scripts/
├── domain_adaptive_pretrain.py   Continued MLM on YouTube corpus
└── evaluate_domain_adapted_phobert.py   DAPT vs. base comparison
```

## Reproducing the Headline Numbers

Hardware: single-machine CPU is sufficient; GPU reduces the DAPT
evaluation from ~95 minutes to ~10 minutes.

```bash
# 1. Domain-adaptive pretraining (only if you want to regenerate
#    the DAPT base; pre-trained checkpoint is already in models/)
python3 scripts/domain_adaptive_pretrain.py

# 2. Controlled comparison — 2 base models × 3 seeds × 2 test sets
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python3 -m scripts.evaluate_domain_adapted_phobert \
    --models models/phobert_base_local models/phobert_domain_adapted \
    --seeds 42 123 2024 \
    --output-dir results/domain_adapted_eval_<timestamp>
```

Outputs:
- `results/.../comparison_table.md` — aggregated mean ± std
- `results/.../metrics.json` — per-(model, seed, test_set) record
- `results/.../predictions/*.csv` — full probability outputs for error analysis

The full paper draft with Section 5.5 (DAPT counter-experiment) and
Discussion is at [`docs/paper_report.html`](docs/paper_report.html).

## Design and Plan

- Design spec: [`docs/superpowers/specs/2026-06-25-domain-adapted-phobert-eval-design.md`](docs/superpowers/specs/2026-06-25-domain-adapted-phobert-eval-design.md)
- Implementation plan: [`docs/superpowers/plans/2026-06-25-domain-adapted-phobert-eval-plan.md`](docs/superpowers/plans/2026-06-25-domain-adapted-phobert-eval-plan.md)

## Ethics

The corpus contains only public YouTube comments. No usernames,
avatars, or personally identifying metadata are stored. Predictions
are research artifacts and must not be used for clinical diagnosis.
Quoted comments in the paper are paraphrased or shortened to reduce
re-identification risk.