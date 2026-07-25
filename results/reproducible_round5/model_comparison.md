# Canonical model comparison

Primary metric: macro-F1. VSMEC is an affective cross-domain proxy, not a clinical depression gold standard.

## Clean training data

| Model | Estimate | n seeds | Domain | Accuracy | Precision-M | Recall-M | F1-M | F1-W | F1-Dep |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| TF-IDF + Logistic Regression | single deterministic run | 1 | in-domain | 0.8967 | 0.7376 | 0.8539 | 0.7779 | 0.9068 | 0.6154 |
| TF-IDF + Logistic Regression | single deterministic run | 1 | cross-domain | 0.5152 | 0.6904 | 0.5152 | 0.3705 | 0.3705 | 0.0685 |
| TF-IDF + LinearSVC | single deterministic run | 1 | in-domain | 0.9215 | 0.7835 | 0.8324 | 0.8051 | 0.9246 | 0.6545 |
| TF-IDF + LinearSVC | single deterministic run | 1 | cross-domain | 0.5081 | 0.6710 | 0.5081 | 0.3543 | 0.3543 | 0.0393 |
| PhoBERT | multi-seed mean/std | 3 | in-domain | 0.9160 ± 0.0086 | 0.7750 ± 0.0251 | 0.7821 ± 0.0254 | 0.7771 ± 0.0152 | 0.9167 ± 0.0066 | 0.6012 ± 0.0273 |
| PhoBERT | multi-seed mean/std | 3 | cross-domain | 0.5096 ± 0.0027 | 0.7389 ± 0.0115 | 0.5096 ± 0.0027 | 0.3549 ± 0.0063 | 0.3549 ± 0.0063 | 0.0389 ± 0.0115 |
| PhoBERT majority vote | majority-vote point estimate | 3 | in-domain | 0.9174 | 0.7770 | 0.7770 | 0.7770 | 0.9174 | 0.6000 |
| PhoBERT majority vote | majority-vote point estimate | 3 | cross-domain | 0.5075 | 0.7319 | 0.5075 | 0.3502 | 0.3502 | 0.0306 |
| BiLSTM (random embeddings) | multi-seed mean/std | 3 | in-domain | 0.8678 ± 0.0488 | 0.6998 ± 0.0535 | 0.7434 ± 0.0566 | 0.7022 ± 0.0231 | 0.8775 ± 0.0303 | 0.4811 ± 0.0164 |
| BiLSTM (random embeddings) | multi-seed mean/std | 3 | cross-domain | 0.5237 ± 0.0237 | 0.6177 ± 0.0240 | 0.5237 ± 0.0237 | 0.3998 ± 0.0568 | 0.3998 ± 0.0568 | 0.1278 ± 0.1068 |
| BiLSTM (frozen PhoBERT embeddings) | multi-seed mean/std | 3 | in-domain | 0.9036 ± 0.0120 | 0.7412 ± 0.0329 | 0.7398 ± 0.0169 | 0.7402 ± 0.0247 | 0.9037 ± 0.0105 | 0.5343 ± 0.0424 |
| BiLSTM (frozen PhoBERT embeddings) | multi-seed mean/std | 3 | cross-domain | 0.5240 ± 0.0032 | 0.6512 ± 0.0077 | 0.5240 ± 0.0032 | 0.3971 ± 0.0063 | 0.3971 ± 0.0063 | 0.1206 ± 0.0112 |
| BERTopic-only + Logistic Regression | single deterministic run | 1 | in-domain | 0.4339 | 0.4828 | 0.4543 | 0.3625 | 0.5318 | 0.1491 |
| BERTopic-only + Logistic Regression | single deterministic run | 1 | cross-domain | 0.4877 | 0.4871 | 0.4877 | 0.4819 | 0.4819 | 0.5367 |
| PhoBERT + BERTopic | single seed-42 feature model | 1 | in-domain | 0.9008 | 0.7384 | 0.8031 | 0.7649 | 0.9067 | 0.5862 |
| PhoBERT + BERTopic | single seed-42 feature model | 1 | cross-domain | 0.5175 | 0.7030 | 0.5175 | 0.3747 | 0.3747 | 0.0758 |

## Augmented training data

| Model | Estimate | n seeds | Domain | Accuracy | Precision-M | Recall-M | F1-M | F1-W | F1-Dep |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| TF-IDF + Logistic Regression | single deterministic run | 1 | in-domain | 0.9132 | 0.7665 | 0.8808 | 0.8084 | 0.9208 | 0.6667 |
| TF-IDF + Logistic Regression | single deterministic run | 1 | cross-domain | 0.5217 | 0.6897 | 0.5217 | 0.3858 | 0.3858 | 0.0968 |
| TF-IDF + LinearSVC | single deterministic run | 1 | in-domain | 0.9215 | 0.7869 | 0.7970 | 0.7918 | 0.9222 | 0.6275 |
| TF-IDF + LinearSVC | single deterministic run | 1 | cross-domain | 0.5117 | 0.6696 | 0.5117 | 0.3635 | 0.3635 | 0.0564 |
