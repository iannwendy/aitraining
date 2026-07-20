# Data Directory Structure

This directory contains all datasets for the Vietnamese Depression Detection project.

## Directory Structure

```
data/
├── _archive/                 # Obsolete/backup files from previous iterations
│
├── raw/                      # Raw crawled and processed data
│   ├── raw_comments.csv      # Raw YouTube comments
│   ├── cleaned_comments.csv  # Cleaned comments
│   ├── video_metadata.csv    # Video metadata
│   ├── processed_videos.txt  # List of processed video IDs
│   └── auto_labeled_comments.csv  # Weak-labeled comments
│
├── labeled/                  # Labeled datasets for training
│   ├── initial_train.csv    # Initial training set
│   ├── gold_review.csv      # Gold review set
│   ├── final_dataset.csv    # Final dataset (all rounds)
│   ├── train.csv / val.csv / test.csv  # Train/val/test splits
│   ├── final_train.csv / final_val.csv / final_test.csv  # Final splits
│   ├── train_gold.csv / val_gold.csv / test_gold.csv  # Gold splits
│   └── final_train_augmented*.csv  # Augmented versions
│
├── model_predictions/        # Model prediction outputs
│   ├── phobert_active_learning_samples.csv
│   ├── phobert_confident_predictions.csv
│   ├── phobert_remaining_predictions.csv
│   └── review_samples.csv
│
├── analysis/                 # Analysis and error reports
│   ├── baseline_gold_errors.csv
│   ├── review_eval_errors.csv
│   ├── labeling_report.json
│   ├── review_eval_report.json
│   └── bertopic_thesis_export.json
│
├── round1/ / round2/ / round3/ / round4/ / round5/  # Round-specific data
│
├── augmented_v1/             # Augmented dataset version 1
│   ├── final_dataset_aug.csv
│   ├── final_train_aug.csv
│   ├── final_val_aug.csv
│   └── final_test_aug.csv
│
└── predictions.db           # SQLite database (not tracked in git)
```

## Dataset Naming Conventions

- `*_gold.csv` - Gold standard (human annotated)
- `*_final*.csv` - Final version after all rounds
- `*_augmented*.csv` - Data with augmentation
- `*.backup_*.csv` - Backup files
- `*.v1_obsolete.csv` - Obsolete version 1 files (in _archive)

## Data Flow

1. **Raw** → Crawled YouTube comments
2. **Labeled** → Cleaned & annotated datasets
3. **Model Predictions** → PhoBERT predictions for active learning
4. **Round folders** → Round-specific training data

## Last Reorganized

2026-07-20: Files reorganized by data type (raw, labeled, predictions, analysis).
