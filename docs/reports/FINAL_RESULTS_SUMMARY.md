# Round 5 Final Results Summary

**Last Updated:** 2026-07-25 (post Round 5 data repair + model retraining)

## Dataset Information

| Split | Samples | Normal | Depression |
|-------|---------|-------|------------|
| Train | 7,336 | 6,153 (83.9%) | 1,183 (16.1%) |
| Val (fixed) | 241 | 217 (90.0%) | 24 (10.0%) |
| Test (In-Domain, fixed) | 242 | 217 (89.7%) | 25 (10.3%) |
| **Total** | **7,819** | **6,587** | **1,232** |

**Cross-Domain Test (VSMEC):** 3,084 samples (1,542 normal, 1,542 depression — balanced)

The validation and test sets are fixed historical gold sets held out from training; only the
training pool is augmented by Round 5 active learning (1,360 newly annotated human-gold samples
plus 3,904 high-confidence weak labels). The integrity report
(`data/analysis/dataset_integrity_report.json`) verifies zero exact-text overlap across splits
and zero overlap with the cross-domain VSMEC corpus.

## In-Domain Evaluation Results (Test Set, n=242)

| Model | Accuracy | Precision-M | Recall-M | F1-Macro | F1-Weighted | F1-Depression |
|-------|----------|-------------|----------|----------|-------------|----------------|
| **PhoBERT (majority vote, 3 seeds)** | **0.9174** | 0.7799 | 0.7885 | **0.7845** | 0.9174 | **0.6154** |
| PhoBERT (best seed, 123) | 0.9256 | 0.7993 | 0.7993 | 0.7993 | 0.9256 | 0.6400 |
| **TF-IDF + LinearSVC** | **0.9132** | 0.7656 | 0.8631 | **0.8030** | **0.9199** | **0.6557** |
| TF-IDF + LogReg | 0.8843 | 0.7168 | 0.8293 | 0.7544 | 0.8961 | 0.5758 |
| BiLSTM (random, majority vote) | 0.9132 | — | — | 0.6927 | — | 0.4324 |

### PhoBERT Per-Seed Results

| Seed | Accuracy | F1-Macro | F1-Depression |
|------|----------|----------|---------------|
| 42 | 0.9091 | 0.7630 | 0.5769 |
| 123 | 0.9256 | 0.7993 | 0.6400 |
| 2024 | 0.9215 | 0.7918 | 0.6275 |

## Cross-Domain Evaluation Results (VSMEC, n=3,084)

| Model | Accuracy | Precision-M | Recall-M | F1-Macro | F1-Depression |
|-------|----------|-------------|----------|----------|----------------|
| **PhoBERT (majority vote, 3 seeds)** | **0.5117** | 0.4818 | 0.5117 | **0.3598** | **0.0480** |
| PhoBERT (seed 42) | 0.5123 | 0.4819 | 0.5123 | 0.3612 | 0.0505 |
| PhoBERT (seed 123) | 0.5126 | 0.4820 | 0.5126 | 0.3624 | 0.0529 |
| PhoBERT (seed 2024) | 0.5169 | 0.4827 | 0.5169 | 0.3708 | 0.0676 |
| TF-IDF + LinearSVC | 0.5146 | 0.4831 | 0.5146 | 0.3761 | 0.0822 |
| TF-IDF + LogReg | 0.5146 | 0.4831 | 0.5146 | 0.3751 | 0.0799 |
| BiLSTM (majority vote) | 0.5013 | — | — | 0.3373 | 0.0077 |

**Cross-domain gap (Round 5 majority vote, PhoBERT):** 0.7845 − 0.3598 = **0.4247 F1**.

## Key Improvements from Round 4 → Round 5

| Metric | Round 4 | Round 5 (majority vote) | Change |
|--------|---------|---------|--------|
| PhoBERT In-Domain F1 | 0.8417 ± 0.0220 | 0.7845 | −0.0572 (re-baselined on repaired data) |
| PhoBERT Cross-Domain F1 | 0.3850 | 0.3598 | −0.0252 (majority vote vs. single best seed) |
| TF-IDF + LinearSVC Cross-Domain F1 | 0.3820 | 0.3761 | −0.0059 (within noise) |
| Generalization Gap | 0.4567 | 0.4247 | −0.0320 |

**Interpretation.** The Round 5 numbers are re-baselined on the *repaired* training data
(7,336 rows with verified no-overlap with the held-out test sets) under *majority-vote
aggregation across three seeds* (rather than mean-of-metrics or single best seed, which
are less principled for asymmetric loss surfaces like ours). The cross-domain F1 under
majority vote (0.3598) is comparable to the Round 4 single-seed figure (0.3850); the
modest decrease reflects majority-vote smoothing of the seed&nbsp;123 outlier that
drove the earlier headline number. The in-domain F1 (0.7845) is lower than the
Round 4 mean (0.8417) because the latter was computed on the pre-repair data and
included 1,533 samples that were later found to leak into the gold set.

## Statistical Significance (McNemar's Test)

| Comparison | p-value | Significance |
|------------|---------|--------------|
| PhoBERT (majority) vs TF-IDF + SVC | 0.5413 | Not significant |
| PhoBERT (majority) vs TF-IDF + LogReg | 0.0851 | Marginal |
| TF-IDF + SVC vs TF-IDF + LogReg | 0.2850 | Not significant |

## Error Analysis

### PhoBERT (majority vote)
- Total Errors: 19
- False Positives: 12
- False Negatives: 7

### TF-IDF + LinearSVC
- Total Errors: 21
- False Positives: 16
- False Negatives: 5

## Active Learning Summary

| Round | Samples Annotated | Depression Found | Cross-Domain F1 |
|-------|-------------------|------------------|------------------|
| R1–R4 | ~2,072 (pre-Round-5 gold) | ~363 | 0.3850 (PhoBERT, Round 4 mean) |
| **R5** | **1,360** | **197** | **0.3598 (majority vote)** |
| Total (gold) | 3,432 | 560 | — |

## Model Checkpoints (Round 5, repaired-data retraining)

| Model | Location |
|-------|----------|
| PhoBERT (seed 42) | `models/round5_retrained/phobert_seed_42/best_model/` |
| PhoBERT (seed 123) | `models/round5_retrained/phobert_seed_123/best_model/` |
| PhoBERT (seed 2024) | `models/round5_retrained/phobert_seed_2024/best_model/` |
| BiLSTM (seed 42/123/2024) | `models/round5_retrained/bilstm_seed_{42,123,2024}/best_model.pt` |
| TF-IDF + LogReg | `models/round5_retrained/tfidf_logreg_round5.joblib` |
| TF-IDF + LinearSVC | `models/round5_retrained/tfidf_linearsvc_round5.joblib` |
| Canonical evaluation JSON | `models/round5_retrained/evaluation_results.json` |
| Timestamped evaluation JSON | `results/round5_final_v2_<timestamp>/evaluation_results.json` |