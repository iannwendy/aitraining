# Docs Organization

This directory contains all documentation, reports, datasets, and scripts for the Vietnamese Depression Detection project.

## Directory Structure

```
docs/
├── _archive/                      # Archived/backup files
│   └── figures_backup_20260718/  # Old figure backups
│
├── active_learning/               # Active learning annotation data
│   ├── export_*.csv              # Exported annotation data
│   ├── round3/                   # Round 3 annotations (initial)
│   ├── round4/                   # Round 4 annotations
│   ├── round5/                   # Round 5 annotations
│   └── steps/
│       ├── step5_review/        # Step 5 (regular review)
│       └── step8_active_learning/ # Step 8 (active learning)
│
├── appendices/                    # Paper appendices
│   ├── APPENDIX_*.md            # Main appendices (errors, hyperparameters, keywords)
│   ├── manual_review/           # Label Studio review guides
│   └── review_decision/         # Review decision checklists
│
├── final_fig/                    # Final figures for paper (h1-h9)
│
├── phases/                       # Phase evaluation reports & scripts
│   ├── phase1_eval_report.json
│   ├── phase2_report.json
│   ├── phase3/                  # Phase 3 model training scripts
│   ├── phase3_comparison_report.json
│   └── phase3_phobert_bertopic_metrics.json
│
├── report_pdf/                   # Figures for PDF report
│
├── reports/                      # Progress, round, and training reports
│   ├── FINAL_RESULTS_SUMMARY.md
│   ├── PDF_vs_HTML_comparison_report.md
│   ├── ROADMAP_SAU_REVIEW.md
│   ├── VISUALIZATION_PROPOSAL.md
│   ├── progress/                # Weekly progress reports (YYYY-MM-DD)
│   ├── round/                   # Round selection reports
│   └── training/               # Training reports
│
├── scripts/                      # Python utility scripts
│   ├── merge_round4_active_learning.py
│   ├── merge_round5_active_learning.py
│   ├── phase1_merge_review.py
│   ├── phase2_build_final_dataset.py
│   ├── prepare_label_studio_import.py
│   ├── prepare_round3_active_learning.py
│   └── prepare_round4_active_learning.py
│
├── superpowers/                  # Claude superpowers plans & specs
│   ├── plans/
│   └── specs/
│
└── paper_report.html             # Paper HTML report
```

## File Naming Conventions

### Reports (MD files)
- Progress reports: `PROGRESS_REPORT_YYYY-MM-DD.md`
- Round reports: `round{N}_report.md` or `round{N}_selection_report.json`
- Training reports: `TRAINING_REPORT_YYYY-MM-DD.md`

### Active Learning Data (CSV)
- Import files: `label_studio_round{N}_active_learning_import.csv`
- Key files: `label_studio_round{N}_active_learning_key.csv`
- Merged files: `*_MERGED.csv`
- Backup files: `*.backup_*.csv`

### Phase Reports (JSON)
- Phase evaluations: `phase{N}_*_report.json`
- Metrics: `phase{N}_*_metrics.json`

## Last Reorganized

2026-07-20: Files reorganized by round, date, and phase for better traceability.
