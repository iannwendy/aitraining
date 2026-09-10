# Vietnamese Depression Detection - Dataset Documentation

## 📁 Data Access

**GitHub Repository:** https://github.com/iannwendy/aitraining

**Data Directory:** https://github.com/iannwendy/aitraining/tree/main/data

---

## 📋 Dataset Description

This dataset contains Vietnamese YouTube comments labeled for depression detection, collected and annotated through multiple rounds of active learning. The data is used for training and evaluating machine learning models for binary classification (depression risk: yes/no).

### Data Format

All CSV files follow this schema:

| Column | Type | Description |
|--------|------|-------------|
| `text` | string | Vietnamese text (comment content) |
| `label` | int | 0 = no depression risk, 1 = depression risk |
| `source` | string | Data source (youtube, reddit, etc.) |
| `round` | int | Annotation round number |
| `video_id` | string | YouTube video ID (for YouTube comments) |

---

## 📂 Directory Structure

### `raw/` - Raw Crawled Data
```
raw/
├── raw_comments.csv          # Raw YouTube comments (before cleaning)
├── cleaned_comments.csv       # Cleaned comments
├── video_metadata.csv         # Video metadata
├── processed_videos.txt       # List of processed video IDs
└── auto_labeled_comments.csv  # Weak-labeled via keywords
```

### `labeled/` - Labeled Training Datasets
```
labeled/
├── gold_review.csv            # Gold standard set (human-annotated)
├── final_dataset.csv          # Complete dataset (all rounds combined)
├── train.csv / val.csv / test.csv           # Initial splits (80/10/10)
├── final_train.csv / final_val.csv / final_test.csv  # Final splits
└── train_gold.csv / val_gold.csv / test_gold.csv    # Gold-only splits
```

### `round1/` - `round6/` - Round-Specific Data
Each round folder contains annotations from that specific iteration:
```
round5/
├── round5_reviewed_clean.csv  # Clean annotations from round 5
round6/
├── round6_reviewed_clean.csv  # Clean annotations from round 6
```

### `augmented_v1/` & `augmented_v2/` - Augmented Datasets
Data expanded via back-translation and synthetic generation:
```
augmented_v2/
├── final_dataset_aug.csv      # Complete augmented dataset
├── final_train_aug.csv        # Training split
├── final_val_aug.csv          # Validation split
└── final_test_aug.csv         # Test split
```

### `translated/` - Translated Data
```
translated/
└── reddit_dep_translated.csv   # Reddit depression posts (translated to Vietnamese)
```

### `analysis/` - Analysis Reports
```
analysis/
├── dataset_integrity_report_round6_v2.json    # Data quality report
├── labeling_report.json                        # Labeling statistics
└── bertopic_thesis_export.json                 # Topic analysis
```

---

## 🔗 Dataset Files for Reproduction

### For Training Models
| File | Link | Description |
|------|------|-------------|
| `final_dataset.csv` | [GitHub](https://github.com/iannwendy/aitraining/blob/main/data/labeled/final_dataset.csv) | Main dataset |
| `final_train.csv` / `final_val.csv` / `final_test.csv` | [GitHub](https://github.com/iannwendy/aitraining/tree/main/data/labeled) | Train/Val/Test splits |
| `augmented_v2/final_train_aug.csv` | [GitHub](https://github.com/iannwendy/aitraining/blob/main/data/augmented_v2/final_train_aug.csv) | Augmented training data |

### For Analysis
| File | Link | Description |
|------|------|-------------|
| `gold_review.csv` | [GitHub](https://github.com/iannwendy/aitraining/blob/main/data/labeled/gold_review.csv) | Gold standard (annotated subset) |
| `analysis/dataset_integrity_report_round6_v2.json` | [GitHub](https://github.com/iannwendy/aitraining/blob/main/data/analysis/dataset_integrity_report_round6_v2.json) | Data quality report |

---

## 🚀 How to Use This Data

### Clone and Access
```bash
# Clone the repository
git clone https://github.com/iannwendy/aitraining.git

# Navigate to data directory
cd aittraining/data

# Or download specific file
curl -O https://raw.githubusercontent.com/iannwendy/aitraining/main/data/labeled/final_dataset.csv
```

### Load in Python
```python
import pandas as pd

# Load main dataset
df = pd.read_csv('https://raw.githubusercontent.com/iannwendy/aitraining/main/data/labeled/final_dataset.csv')

# Load augmented data
df_aug = pd.read_csv('https://raw.githubusercontent.com/iannwendy/aitraining/main/data/augmented_v2/final_train_aug.csv')

print(f"Dataset size: {len(df)} samples")
print(f"Label distribution:\n{df['label'].value_counts()}")
```

---

## 📊 Dataset Statistics

### Label Distribution
| Label | Description | Count |
|-------|-------------|-------|
| 0 | No depression risk | ~majority |
| 1 | Depression risk | ~minority |

### Data Sources
- **YouTube Comments**: Crawled from Vietnamese videos related to mental health, depression, and related topics
- **Reddit**: Translated depression-related posts (in `translated/` folder)

---

## 📝 Citation

If you use this dataset in your research, please cite:

```
Vietnamese Depression Detection Dataset
https://github.com/iannwendy/aitraining
```

---

## 📞 Contact

For questions about the dataset, please refer to the main repository issues page:
https://github.com/iannwendy/aitraining/issues

---

**Last Updated:** September 2026
