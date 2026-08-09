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

**Table 1 — Final model results (9,134 gold samples; 70/15/15 stratified split).**

| Model               | In-domain F1-macro | Cross-domain F1-macro | Generalization Gap |
|---------------------|--------------------|----------------------|--------------------|
| **PhoBERT (majority vote, 3 seeds)** | **0.7254** | 0.3659 | 0.3595 |
| PhoBERT + BERTopic | 0.7153 | 0.3674 | 0.3479 |
| TF-IDF + LogReg | 0.7138 | 0.3577 | 0.3561 |
| TF-IDF + LinearSVC | 0.7025 | **0.3798** | 0.3227 |
| BiLSTM (majority vote) | 0.6421 | 0.3375 | 0.3046 |
| BERTopic-only | 0.4208 | 0.5030 | -0.0822 |

_Results evaluated on: In-domain test (n=1,371, 271 depression), Cross-domain VSMEC (n=3,084, balanced 50/50).
PhoBERT numbers are majority-vote aggregation across three seeds (42, 123, 2024)._

**Dataset Split (70/15/15 stratified):**
- Train: 6,392 samples (1,262 depression, 19.7%)
- Validation: 1,371 samples (271 depression, 19.8%)
- Test: 1,371 samples (271 depression, 19.8%)

**Key Findings.**

1. **PhoBERT achieves the highest in-domain F1-macro** (0.7254), confirming the advantage of pretrained language models for Vietnamese NLP.

2. **TF-IDF + LinearSVC achieves the best cross-domain F1-macro** (0.3798), suggesting that simpler models generalize better across domains.

3. **The generalization gap is data-centric**, not architecture-centric. Four factors contribute: label definition divergence, text length mismatch, linguistic register divergence, and class imbalance.

4. **Larger training sets do not close the gap.** Active learning across six rounds (9,134 gold samples) did not improve cross-domain F1 beyond earlier baselines.

## Data Artifacts

| Artifact                                       | Size        | Purpose                                |
|------------------------------------------------|-------------|----------------------------------------|
| `data/cleaned_comments.csv`                    | 125,329 rows | Cleaned YouTube comments              |
| `data/labeled/train_gold.csv`                  | 9,134 rows   | Human-reviewed gold samples (R5 + R6) |
| `data/labeled/final_dataset.csv`               | 9,134 rows   | All gold samples (70/15/15 split)     |
| `data/labeled/final_train.csv`                | 6,392 rows   | Training set (70%)                     |
| `data/labeled/final_val.csv`                   | 1,371 rows   | Validation set (15%)                   |
| `data/labeled/final_test.csv`                  | 1,371 rows   | In-domain test set (15%)               |
| `data/round6/round6_reviewed_clean.csv`       | 5,702 rows   | Round 6 human-labeled samples         |
| `data_unified/cross_domain_test.csv`           | 3,084 rows   | VSMEC cross-domain test (held out)    |
| `data_unified/corpus_text_all.csv`             | 316,401 rows | YouTube + 8 external Vietnamese sets   |

## Models

| Model               | Code path                                            | In-domain / Cross-domain F1-Macro |
|---------------------|------------------------------------------------------|-----------------|
| PhoBERT (majority vote) | `models/round6_v2_retrained/phobert_seed_*/best_model/` | 0.7254 / 0.3659 |
| PhoBERT + BERTopic | Combined features                                      | 0.7153 / 0.3674 |
| TF-IDF + LogReg    | `models/round6_v2_retrained/tfidf_logreg_round6.joblib` | 0.7138 / 0.3577 |
| TF-IDF + LinearSVC | `models/round6_v2_retrained/tfidf_linearsvc_round6.joblib` | 0.7025 / 0.3798 |
| BiLSTM (majority vote) | `models/round6_v2_retrained/bilstm_seed_*/best_model.pt` | 0.6421 / 0.3375 |
| BERTopic-only | `models/bertopic/bertopic_model.pkl`                   | 0.4208 / 0.5030 |

## Reproducing Results

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Merge gold samples and create stratified split
PYTHONPATH="$PWD" .venv/bin/python scripts/merge_gold_samples.py

# 3. Retrain all models
PYTHONPATH="$PWD" .venv/bin/python scripts/retrain_all_models_round6.py

# 4. Run evaluation
PYTHONPATH="$PWD" .venv/bin/python scripts/run_final_round6_evaluation.py
PYTHONPATH="$PWD" .venv/bin/python scripts/evaluate_bertopic_round6.py
```

## Ethics

The corpus contains only public YouTube comments. No usernames,
avatars, or personally identifying metadata are stored. Predictions
are research artifacts and must not be used for clinical diagnosis.
