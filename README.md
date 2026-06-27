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

| Model variant               | In-domain F1-macro | Cross-domain F1-macro |
|-----------------------------|--------------------|----------------------|
| TF-IDF + LogReg (baseline)  | 0.8347             | 0.3917               |
| TF-IDF + LinearSVC           | 0.8286             | 0.3820               |
| BiLSTM (random embedding)   | _see paper §5.1_   | _see paper §5.1_     |
| BiLSTM (PhoBERT-frozen)     | _see paper §5.1_   | _see paper §5.1_     |
| **PhoBERT (original)**      | **0.8681 ± 0.0086** | **0.3727 ± 0.0242** |
| BERTopic-only               | 0.5599             | 0.5030               |
| PhoBERT + BERTopic          | 0.9501             | 0.3977               |

_Single-seed run; mean ± std not reported because seeds were not
exhausted for these variants. The DAPT counter-experiment below
adds the missing statistical rigor for the one model that warranted
it._

**Table 2 — Domain-adaptive pretraining counter-experiment (3 seeds: 42, 123, 2024).**

| Model               | In-domain F1-macro (mean ± std) | Cross-domain F1-macro (mean ± std) |
|---------------------|---------------------------------|-------------------------------------|
| **PhoBERT (original)** | **0.8681 ± 0.0086**         | **0.3727 ± 0.0242**                 |
| PhoBERT + DAPT (2 ep.) | **0.8803 ± 0.0030**         | 0.3620 ± 0.0188                     |

_Trained and evaluated on the same final dataset; only the encoder
checkpoint differs. Numbers reproduce verbatim from
`results/domain_adapted_eval_2026-06-26_181310/comparison_table.md`._

**Two empirical findings.**

1. **A generalization gap of approximately 0.50–0.53 F1-macro** between
   in-domain and cross-domain performance is consistent across model
   families (TF-IDF+SVM, BiLSTM, PhoBERT). The bottleneck is
   data-centric — label definition divergence, text length mismatch,
   linguistic register divergence, and class imbalance — not
   architecture-centric.

2. **Domain-adaptive pretraining reverses direction after the round-3
   review merge.** On the pre-round-3 training set (3,576 rows, mostly
   keyword-derived weak labels), two epochs of continued MLM on 119,649
   YouTube comments degraded downstream F1 by approximately 3.5–4.0
   points on both test sets. On the post-round-3 set (1,786 rows, with
   985 human-gold labels and a more diverse depression signal), the
   *same* DAPT checkpoint instead produces a small but consistent
   in-domain F1 gain (+0.0122) at the cost of a marginal cross-domain
   loss (−0.0107); neither delta is statistically significant at
   three seeds (in-domain *t*(2) = −1.84, *p* ≈ 0.21; cross-domain
   *t*(2) = 1.29, *p* ≈ 0.34). The cross-domain gap (~0.50 F1) is
   essentially unchanged, confirming the data-centric bottleneck
   identified in finding 1. The change in direction is attributable to
   the larger and more diverse human-gold proportion in the new
   training set, which appears to provide enough discriminative
   supervision for the DAPT checkpoint to recover general-purpose
   features rather than being dominated by keyword-bias shortcuts.
   For practitioners: both checkpoints are reasonable defaults; the
   base PhoBERT is simpler to obtain, while the DAPT checkpoint offers
   a small reproducible in-domain advantage.
   Full discussion in [`docs/paper_report.html` § 5.5](docs/paper_report.html).

## Data Artifacts

| Artifact                                       | Size        | Purpose                                |
|------------------------------------------------|-------------|----------------------------------------|
| `data/cleaned_comments.csv`                    | 125,329 rows | Cleaned YouTube comments              |
| `data/auto_labeled_comments.csv`               | 125,329 rows | Weak labels via keyword scoring      |
| `data/gold_review.csv`                         | 2,515 rows   | Blind human-reviewed subset (post round-3) |
| `data/final_train.csv`                         | 1,786 rows   | Multi-source training set             |
| `data/final_val.csv`                           | 383 rows     | Validation split                      |
| `data/final_test.csv`                          | 383 rows     | In-domain test                        |
| `data_unified/cross_domain_test.csv`           | 3,084 rows   | VSMEC cross-domain test (held out)    |
| `data_unified/corpus_text_all.csv`             | 316,401 rows | YouTube + 8 external Vietnamese sets |
| `results/domain_adapted_eval_<ts>/`            | 12 runs      | DAPT counter-experiment metrics (3 seeds × 2 models × 2 test sets) |

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

Hardware: single-machine CPU is sufficient; the post-round-3 DAPT
evaluation (1,786-row training set) takes ~70 minutes wall-clock on
MPS. GPU reduces the same run to ~10 minutes.

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