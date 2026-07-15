#!/usr/bin/env python3
"""
update_figures.py - Update paper_report.html with new LaTeX figures and academic captions

Usage:
    python update_figures.py [--dry-run]

This script:
1. Replaces figure paths with LaTeX-generated versions
2. Updates captions to academic format
3. Adds proper references to Table/Figure numbers
"""

import re
import os
import argparse
from datetime import datetime

# Path configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "..", "paper_report.html")
BACKUP_PATH = os.path.join(SCRIPT_DIR, "..", f"paper_report_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

# LaTeX figure paths (relative to docs/)
LATEX_FIGURES = {
    "fig-c1-01-conceptual-framework": "latex_figures/pdf/fig_c1_framework.pdf",
    "fig-3-1-weak-label-distribution": "latex_figures/pdf/fig3_1_weak_label.pdf",
    "fig-c2-01-method-taxonomy": "latex_figures/pdf/fig_c2_taxonomy.pdf",
    "fig-c4-01-pipeline": "latex_figures/pdf/fig_c4_pipeline.pdf",
    "fig-5-1-generalization-gap": "latex_figures/pdf/fig5_1_generalization_gap.pdf",
    "fig-5-2-bertopic-topics": "latex_figures/pdf/fig5_2_bertopic_topics.pdf",
    "fig-5-3-confusion-matrices": "latex_figures/pdf/fig5_3_confusion_matrices.pdf",
    "fig-5-4-dapt-counter-experiment": "latex_figures/pdf/fig5_4_dapt_experiment.pdf",
    "fig-augmentation": "latex_figures/pdf/fig_augmentation.pdf",
}

# Academic captions (replacements)
ACADEMIC_CAPTIONS = {
    "fig-c1-01-conceptual-framework": {
        "short": "Figure 1.1",
        "new": """<strong>Figure 1.1.</strong> Conceptual framework illustrating the three-layer architecture of this study. <em>Layer 1 (Clinical Reality)</em>: Major Depressive Disorder (MDD) according to DSM-5 criteria and validated screening instruments (PHQ-9, BDI-II), alongside structural barriers to early detection in Vietnam—stigma, limited mental health workforce (0.2 psychiatrists per 100,000 population), and self-report instrument requirements. <em>Layer 2 (Social Media Signal)</em>: Vietnamese-language YouTube comments (N = 125,329) as ecologically valid linguistic data reflecting psychological states. <em>Layer 3 (This Work)</em>: End-to-end machine learning pipeline comprising weak-labeling, blind human annotation, model training, and two-domain evaluation. Evaluation boxes (orange) highlight the empirical contribution: in-domain (YouTube, n = 912) versus cross-domain (VSMEC, n = 3,084) assessment of model generalization (ΔF1 ≈ 0.37)."""
    },
    "fig-3-1-weak-label-distribution": {
        "short": "Figure 3.1",
        "new": """<strong>Figure 3.1.</strong> Weak-label distribution across the 125,329 cleaned YouTube comments. The overwhelming majority of comments (78.52%, n = 98,410) fall into the <code>uncertain</code> category, reflecting insufficient lexical signals for automated classification. High-confidence <code>depression_auto</code> labels (0.62%, n = 779) and <code>normal_auto</code> labels (2.75%, n = 3,449) represent the clearest cases. The high <code>need_review</code> rate (96.01%) motivates the heavy reliance on blind human annotation rather than direct weak-label training."""
    },
    "fig-c2-01-method-taxonomy": {
        "short": "Figure 2.1",
        "new": """<strong>Figure 2.1.</strong> Methodological taxonomy of NLP approaches to depression detection from user-generated text. Three branches: (1) <em>Lexicon-based</em> methods (LIWC, ANEW) are context-blind and language-specific; (2) <em>Traditional ML</em> methods (TF-IDF + SVM/LR/RF) require manual feature engineering with shallow semantic representations; (3) <em>Deep Learning</em> methods leverage pretrained transformers. Domain-adapted variants (MentalBERT, PsychBERT) are English-only. PhoBERT (highlighted in green) is the Vietnamese-specific architecture evaluated in this work, achieving F1-macro = 0.8596 (in-domain) and 0.4937 (cross-domain) on Round 5 data."""
    },
    "fig-c4-01-pipeline": {
        "short": "Figure 4.1",
        "new": """<strong>Figure 4.1.</strong> Model training and evaluation phase within the overall research pipeline. <em>Chapter 3</em> (blue layer): data acquisition pipeline spanning Steps 1–10 (crawl → clean → external datasets → unified corpus → weak-label → blind annotation → gold set → final dataset assembly). <em>Chapter 4</em> (green layer): model training pipeline comprising Steps 11–15. Step 11: Build final_dataset.csv (N = 6,080, multi-source). Steps 12–13: Train five model architectures and BERTopic. Step 14: In-domain evaluation (YouTube, n = 912). Step 15: Cross-domain evaluation (VSMEC, n = 3,084)."""
    },
    "fig-5-1-generalization-gap": {
        "short": "Figure 5.1",
        "new": """<strong>Figure 5.1.</strong> Generalization gap between in-domain (YouTube, n = 912) and cross-domain (VSMEC, n = 3,084) F1-macro across five model architectures (Round 5 results). Error bars represent ±1 standard deviation over three random seeds (42, 123, 2024) for PhoBERT and BiLSTM. Δ values quantify the in-domain minus cross-domain gap. PhoBERT with majority voting achieves the smallest gap (Δ = 0.366) while maintaining competitive in-domain performance (F1 = 0.8596). BERTopic-only is the sole architecture with higher cross-domain than in-domain F1, attributable to its unsupervised topic features transferring uniformly across domains."""
    },
    "fig-5-2-bertopic-topics": {
        "short": "Figure 5.2",
        "new": """<strong>Figure 5.2.</strong> Top 20 BERTopic topics by document count in the 316,401-document corpus. Bars highlighted in vermillion correspond to the five depression-related thematic clusters (Topic IDs 33, 7, 14, 19, 27). Outlier documents (Topic −1: 48.30%, n = 149,650) are not shown individually. The high outlier rate is characteristic of social media corpora with long-tail content diversity. Topic 33 (trầm_cảm, loạn, thuốc, bệnh) captures clinical depression discourse; Topic 7 (bs, giấc, ngủ, thuốc) relates to sleep disorders and medical consultation; Topic 19 (burnout, work, stress) reflects workplace burnout (predominantly English texts); Topic 14 (khóc, nghe, buồn) captures sadness expression through music; Topic 27 (thân, giấc, ai, cô, buồn) represents loneliness and existential distress."""
    },
    "fig-5-3-confusion-matrices": {
        "short": "Figure 5.3",
        "new": """<strong>Figure 5.3.</strong> Confusion matrices for five model variants on in-domain (YouTube, n = 912) and cross-domain (VSMEC, n = 3,084) test sets. Diagonal cells represent correct predictions (TN, TP); off-diagonal cells represent false positives (FP) and false negatives (FN). In-domain matrices concentrate mass on the diagonal, indicating strong classification performance. Cross-domain matrices are dominated by the true-normal column, reflecting systematic depression-class underprediction. BERTopic-only achieves the highest cross-domain depression recall (F1-depression = 0.5566) despite near-random overall accuracy, owing to its topic-based representations transferring across domains."""
    },
    "fig-5-4-dapt-counter-experiment": {
        "short": "Figure 5.4",
        "new": """<strong>Figure 5.4.</strong> Domain-adaptive pretraining (DAPT) counter-experiment: per-seed F1-macro scores for PhoBERT (original) versus PhoBERT + DAPT across three random seeds (42, 123, 2024). <em>Top panel (In-domain)</em>: DAPT produces a small, consistent gain (+0.0122 F1) across all seeds. <em>Bottom panel (Cross-domain)</em>: DAPT incurs a marginal, inconsistent loss (−0.0107 F1). Neither delta achieves statistical significance at α = 0.05 (in-domain: t(2) = −1.84, p ≈ 0.21; cross-domain: t(2) = 1.29, p ≈ 0.34). The 0.50 F1 cross-domain gap is essentially unchanged by encoder-side adaptation, confirming the data-centric nature of the generalization bottleneck."""
    },
    "fig-augmentation": {
        "short": "Figure A1",
        "new": """<strong>Figure A1.</strong> Effect of seven-strategy data augmentation on model performance. PhoBERT achieves the largest in-domain gain (+9.38 percentage points, F1: 0.8681 → 0.9619). PhoBERT + BERTopic demonstrates the largest cross-domain gain (+12.85 pp, F1: 0.3977 → 0.5262), suggesting that augmented data breaks the model's reliance on domain-specific shortcuts. BERTopic-only remains essentially unchanged (+0.03 pp), confirming that its two-feature representation (topic ID + probability) is the primary bottleneck rather than training data volume. Augmentation strategies: synonym replacement, random insertion/swap/deletion, negation insertion, PhoBERT MLM, and emoticon augmentation."""
    },
}


def update_html(dry_run=True):
    """Update paper_report.html with new figures and captions."""

    # Read HTML file
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create backup
    if not dry_run:
        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Backup created: {BACKUP_PATH}")

    # Count changes
    changes = {
        'figure_paths': 0,
        'captions': 0,
    }

    # Replace figure paths
    for old_path, new_path in LATEX_FIGURES.items():
        pattern = rf'src="([^"]*{old_path}[^"]*)"'
        replacement = f'src="{new_path}"'

        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes['figure_paths'] += 1
            print(f"  [OK] Updated path: {old_path} → {new_path}")

    # Update captions
    for fig_id, caption_data in ACADEMIC_CAPTIONS.items():
        # Find figcaption element
        pattern = rf'<figcaption><strong>{caption_data["short"]}\.</strong>.*?</figcaption>'

        if re.search(pattern, content, re.DOTALL):
            # Keep the short reference, update the rest
            content = re.sub(
                rf'(<figcaption><strong>{caption_data["short"]}\.</strong>).*?(</figcaption>)',
                rf'\1 {caption_data["new"].split("<strong>Figure")[0].strip()}</figcaption>' if False else
                lambda m: caption_data['new'].replace(f'<strong>{caption_data["short"]}.</strong>', f'<strong>{caption_data["short"]}.</strong>'),
                content,
                flags=re.DOTALL
            )
            changes['captions'] += 1
            print(f"  [OK] Updated caption: {caption_data['short']}")

    # Write updated content
    if not dry_run:
        with open(HTML_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nHTML updated: {HTML_PATH}")
    else:
        print(f"\n[Dry-run] Would update: {HTML_PATH}")

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print(f"Figure paths updated: {changes['figure_paths']}/{len(LATEX_FIGURES)}")
    print(f"Captions updated: {changes['captions']}/{len(ACADEMIC_CAPTIONS)}")
    print(f"Mode: {'DRY-RUN (no changes written)' if dry_run else 'LIVE (changes written)'}")

    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update paper_report.html with new LaTeX figures")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--live", action="store_true", help="Actually write changes")
    args = parser.parse_args()

    if args.live:
        update_html(dry_run=False)
    elif args.dry_run:
        update_html(dry_run=True)
    else:
        print("Usage:")
        print("  python update_figures.py --dry-run  # Preview changes")
        print("  python update_figures.py --live      # Write changes")
