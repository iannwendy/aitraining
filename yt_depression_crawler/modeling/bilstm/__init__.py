"""BiLSTM models for Vietnamese depression-sign detection.

Two variants are supported:
- BiLSTMRandom: paper-spec, learned embedding (128d, vocab 15K) + 2-layer
  BiLSTM + classifier. Matches the architecture described in paper
  Section 4.2.
- BiLSTMPhoBERT: PhoBERT word embeddings frozen + 2-layer BiLSTM +
  classifier. Ablation variant — measures how much of the gain comes
  from the encoder's pretraining.

Training uses ``underthesea.word_tokenize`` for Vietnamese segmentation
(matching PhoBERT preprocessing) and applies NO class weighting (per
Appendix B Table of the paper).
"""