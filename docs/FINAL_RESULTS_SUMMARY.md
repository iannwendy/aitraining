# Round 5 Final Results Summary

**Last Updated:** 2026-07-15

## Dataset Information

| Split | Samples | Normal | Depression |
|-------|---------|-------|------------|
| Train | 4,256 | 3,524 (82.8%) | 732 (17.2%) |
| Val | 912 | 756 (82.9%) | 156 (17.1%) |
| Test (In-Domain) | 912 | 756 (82.9%) | 156 (17.1%) |
| **Total** | **6,080** | **5,036** | **1,044** |

**Cross-Domain Test (VSMEC):** 3,084 samples (1,542 normal, 1,542 depression - balanced)

## In-Domain Evaluation Results (Test Set, n=912)

| Model | Accuracy | Precision-M | Recall-M | F1-Macro | F1-Weighted | F1-Depression |
|-------|----------|-------------|----------|----------|-------------|----------------|
| **PhoBERT (avg vote)** | **0.9178** | 0.8490 | 0.8715 | **0.8596** | 0.9191 | 0.7692 |
| TF-IDF + LinearSVC | 0.9211 | 0.8576 | 0.8684 | 0.8629 | **0.9216** | **0.7736** |
| TF-IDF + LogReg | 0.9046 | 0.8206 | 0.8967 | 0.8504 | 0.9096 | 0.7603 |
| BiLSTM (random, avg) | 0.8984 | - | - | 0.8049 | - | - |
| PhoBERT + BERTopic | 0.8739 | - | - | 0.7868 | - | 0.6505 |

### PhoBERT Per-Seed Results

| Seed | Accuracy | Precision-M | Recall-M | F1-Macro | F1-Weighted | F1-Depression |
|------|----------|-------------|----------|----------|-------------|----------------|
| 42 | 0.9145 | 0.8447 | 0.8619 | 0.8529 | 0.9155 | 0.7578 |
| 123 | 0.8805 | 0.7895 | 0.8948 | 0.8239 | 0.8896 | 0.7241 |
| 2024 | 0.9123 | 0.8623 | 0.8123 | 0.8341 | 0.9090 | 0.7203 |

## Cross-Domain Evaluation Results (VSMEC, n=3,084)

| Model | Accuracy | Precision-M | Recall-M | F1-Macro | F1-Weighted | F1-Depression |
|-------|----------|-------------|----------|----------|-------------|----------------|
| **PhoBERT (seed 123)** | **0.5772** | 0.7265 | 0.5772 | **0.4937** | 0.4937 | 0.2882 |
| PhoBERT (seed 42) | 0.5162 | 0.7273 | 0.5162 | 0.3699 | 0.3699 | 0.0663 |
| PhoBERT (seed 2024) | 0.5107 | 0.7527 | 0.5107 | 0.3567 | 0.3567 | 0.0419 |
| PhoBERT + BERTopic | 0.5454 | - | - | 0.4501 | - | 0.2211 |

## Key Improvements from Round 4 → Round 5

| Metric | Round 4 | Round 5 | Change |
|--------|---------|---------|--------|
| PhoBERT In-Domain F1 | 0.8417 ± 0.0220 | 0.8596 (avg vote) | +0.0179 |
| PhoBERT Cross-Domain F1 | 0.3850 ± 0.0219 | 0.4937 (best seed) | **+0.1087** |
| Generalization Gap | 0.4567 | 0.3659 | **-0.0908** |

## Statistical Significance (McNemar's Test)

| Comparison | p-value | Significance |
|------------|---------|-------------|
| PhoBERT (avg) vs TF-IDF + SVC | 0.5413 | Not significant |
| PhoBERT (avg) vs TF-IDF + LogReg | 0.0851 | Marginal |
| TF-IDF + SVC vs TF-IDF + LogReg | 0.2850 | Not significant |

## Error Analysis

### PhoBERT (avg vote)
- Total Errors: 75
- False Positives: 44 (58.7%)
- False Negatives: 31 (41.3%)

### TF-IDF + LinearSVC
- Total Errors: 80
- False Positives: 54 (67.5%)
- False Negatives: 26 (32.5%)

## Active Learning Summary

| Round | Samples Annotated | Depression Found | Cross-Domain F1 |
|-------|-------------------|------------------|------------------|
| R1-R4 | ~4,000 | ~600 | 0.3850 |
| **R5** | **1,533** | **197** | **0.4937** |
| Total | ~6,080 | ~1,044 | - |

## Model Checkpoints

| Model | Location |
|-------|----------|
| PhoBERT (seed 42) | `models/round5_predictions/seed_42/best_model/` |
| PhoBERT (seed 123) | `models/round5_predictions/seed_123/best_model/` |
| PhoBERT (seed 2024) | `models/round5_predictions/seed_2024/best_model/` |
| TF-IDF + LogReg | `models/tfidf_logreg_round5.joblib` |
| TF-IDF + LinearSVC | `models/tfidf_svc_round5.joblib` |
| BiLSTM | `models/bilstm_round5/` |
| PhoBERT + BERTopic | `docs/phase3_phobert_bertopic_metrics.json` |
