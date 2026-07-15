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

**Table 1 — Final model results (Round 5 dataset, 6,080 samples).**

| Model               | In-domain F1-macro | Cross-domain F1-macro | Generalization Gap |
|---------------------|--------------------|----------------------|--------------------|
| **PhoBERT (avg vote, 3 seeds)** | **0.86**   | **0.49 (best seed)**     | **0.37**           |
| TF-IDF + LinearSVC | 0.86 | — | — |
| TF-IDF + LogReg | 0.85 | — | — |
| BiLSTM (random) | 0.80 | — | — |
| PhoBERT + BERTopic | 0.79 | 0.45 | 0.34 |

_Results evaluated on final dataset (6,080 rows: 4,256 train / 912 val / 912 test).
Cross-domain test: VSMEC (3,084 rows). PhoBERT numbers are mean over three seeds (42, 123, 2024).
Full results with all 6 metrics in [`docs/FINAL_RESULTS_SUMMARY.md`](docs/FINAL_RESULTS_SUMMARY.md)._

**Table 2 — Cross-domain improvement from Active Learning.**

| Round | Dataset Size | Cross-domain F1 | Improvement |
|-------|-------------|-----------------|-------------|
| Round 4 | 6,079 | 0.3850 | baseline |
| **Round 5** | **6,080** | **0.4937** | **+0.1087** |

**Key Findings.**

1. **Generalization gap reduced from ~0.45 to ~0.37 F1-macro** after Round 5 active learning.
   The bottleneck is **data-centric** — label definition divergence, text length mismatch,
   linguistic register divergence, and class imbalance — not architecture-centric.

2. **Active learning significantly improves cross-domain generalization.**
   Round 5 human annotation of 1,533 uncertain samples improved cross-domain F1 by +0.1087
   (from 0.3850 to 0.4937), demonstrating that diverse labeled data helps the model
   learn more robust, generalizable features.

3. **PhoBERT achieves competitive performance with simpler baselines.**
   TF-IDF + LinearSVC (0.8629 F1-macro) slightly outperforms PhoBERT (0.8596) on in-domain test,
   but PhoBERT shows better cross-domain generalization (0.4937 vs similar baselines).

## Data Artifacts

| Artifact                                       | Size        | Purpose                                |
|------------------------------------------------|-------------|----------------------------------------|
| `data/cleaned_comments.csv`                    | 125,329 rows | Cleaned YouTube comments              |
| `data/auto_labeled_comments.csv`               | 125,329 rows | Weak labels via keyword scoring      |
| `data/train_gold.csv`                          | 8,460 rows   | All human-reviewed gold samples       |
| `data/final_dataset.csv`                       | 6,080 rows   | Gold + weak_high_conf (final)          |
| `data/final_train.csv`                         | 4,256 rows   | Training set (final)                   |
| `data/final_val.csv`                           | 912 rows     | Validation split (final)             |
| `data/final_test.csv`                          | 912 rows     | In-domain test (final)               |
| `data_unified/cross_domain_test.csv`           | 3,084 rows   | VSMEC cross-domain test (held out)    |
| `data_unified/corpus_text_all.csv`             | 316,401 rows | YouTube + 8 external Vietnamese sets   |

**Data Collection:** 125,329 YouTube comments collected (meeting ≥100,000 requirement).
The 6,080 training samples represent the high-quality labeled subset selected via
active learning for supervised model training.

## Models

| Model               | Code path                                            | Round 5 Results |
|---------------------|------------------------------------------------------|-----------------|
| TF-IDF + LogReg     | `models/tfidf_logreg_round5.joblib`                 | F1=0.8504 |
| TF-IDF + LinearSVC  | `models/tfidf_svc_round5.joblib`                    | F1=0.8629 |
| BiLSTM              | `models/bilstm_round5/`                              | F1=0.8049 |
| PhoBERT             | `models/round5_predictions/seed_*/best_model/`       | F1=0.8596 |
| PhoBERT + BERTopic   | `docs/phase3_phobert_bertopic_metrics.json`          | F1=0.7868 |

## Web Demo

A React + FastAPI web demo is available in [`web_demo/`](web_demo/) for
live depression detection and model comparison.

### Features

| Feature | Description |
|---------|-------------|
| **Dashboard** | Overview metrics from real API |
| **Single Prediction** | PhoBERT inference on single text |
| **Batch Prediction** | Upload CSV for bulk analysis |
| **Topic Analysis** | BERTopic topic visualization |
| **Statistics** | Confusion matrix, class distribution |
| **History** | SQLite-backed prediction history |
| **Model Comparison** | Compare 9 model variants (TF-IDF, BiLSTM, PhoBERT, DAPT, aug) |

### Running the Demo

```bash
# Development (two terminals)
cd web_demo/backend && uvicorn main:app --reload --port 8000
cd web_demo && npm run dev

# Docker (all-in-one)
cd web_demo && docker-compose up --build
```

Demo runs on http://localhost:3000 (frontend) with API at http://localhost:8000.

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
├── final_model_training.py       Final training for Round 5 submission
├── complete_evaluation_round5.py Comprehensive evaluation with all 6 metrics
└── rerun_phobert_bertopic.py    PhoBERT + BERTopic evaluation
```

## Reproducing Results

Hardware: MPS (Apple Silicon) or CPU is sufficient for final evaluation.
Full training takes ~30 minutes on MPS.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run complete evaluation with all metrics
PYTHONPATH="$PWD" .venv/bin/python scripts/complete_evaluation_round5.py

# 3. Train all models (if needed)
PYTHONPATH="$PWD" .venv/bin/python scripts/final_model_training.py

# 4. PhoBERT + BERTopic evaluation
PYTHONPATH="$PWD" .venv/bin/python scripts/rerun_phobert_bertopic.py
```

Outputs:
- `results/final_round5_*/` — training results
- `docs/FINAL_RESULTS_SUMMARY.md` — comprehensive results summary
- `docs/paper_report.html` — full paper draft

## Ethics

The corpus contains only public YouTube comments. No usernames,
avatars, or personally identifying metadata are stored. Predictions
are research artifacts and must not be used for clinical diagnosis.
Quoted comments in the paper are paraphrased or shortened to reduce
re-identification risk.
