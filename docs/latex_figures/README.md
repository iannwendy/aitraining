# LaTeX Figures for Paper

This directory contains LaTeX source files for all figures in the paper, using **TikZ** and **PGFPlots** for publication-quality scientific graphics.

## Figures Included

| Figure | File | Description |
|--------|------|-------------|
| Figure 1.1 | `fig_c1_framework.tex` | Three-layer conceptual framework |
| Figure 2.1 | `fig_c2_taxonomy.tex` | Methodological taxonomy |
| Figure 4.1 | `fig_c4_pipeline.tex` | Pipeline overview |
| Figure 3.1 | `fig3_1_weak_label.tex` | Weak-label distribution |
| Figure 5.1 | `fig5_1_generalization_gap.tex` | Generalization gap comparison |
| Figure 5.2 | `fig5_2_bertopic_topics.tex` | BERTopic top 20 topics |
| Figure 5.3 | `fig5_3_confusion_matrices.tex` | Confusion matrices |
| Figure 5.4 | `fig5_4_dapt_experiment.tex` | DAPT counter-experiment |
| Figure (Aug) | `fig_augmentation.tex` | Data augmentation results |

## Installation

### macOS

```bash
# Install MacTeX (full distribution)
brew install --cask mactex-no-gui

# Or use smaller BasicTeX
brew install --cask basictex
```

After installation, update your PATH:
```bash
export PATH="/usr/local/texlive/2024basic/bin/universal-darwin:$PATH"
```

### Ubuntu/Debian

```bash
sudo apt install texlive-latex-base texlive-pictures texlive-pgfplots texlive-xetex
```

### Windows

1. Download MiKTeX from https://miktex.org/download
2. Install and follow the wizard

## Compilation

### Compile All Figures

```bash
# Make script executable
chmod +x compile_all.sh

# Compile to both PDF and PNG
./compile_all.sh both

# Compile to PDF only
./compile_all.sh pdf

# Compile to PNG only
./compile_all.sh png
```

### Compile Individual Figure

```bash
pdflatex -interaction=nonstopmode fig5_1_generalization_gap.tex
```

### Convert to PNG (requires ImageMagick)

```bash
brew install imagemagick
convert -density 300 fig5_1_generalization_gap.pdf -quality 100 fig5_1_generalization_gap.png
```

## Output

Compiled figures will be in:
- `pdf/` - PDF vector format (for print)
- `png/` - PNG raster format (for web/DOCX)

## Data Used

All figures use the **Round 5** results with the latest data:

| Metric | Value |
|--------|-------|
| PhoBERT F1 (in-domain) | 0.8596 |
| PhoBERT F1 (cross-domain) | 0.4937 |
| Generalization Gap | Δ0.366 |
| Cross-domain improvement | +0.1210 |
| Dataset size | 6,080 samples |
| In-domain test | n=912 |
| Cross-domain test | n=3,084 |
| BERTopic topics | 456 |
| BERTopic outlier rate | 48.30% |

## Customization

### Change Colors

Modify the `cycle list` or `fill` options in each file:

```latex
cycle list={
    {fill=blue!60,draw=blue!80},  % Change blue shade
    {fill=red!60,draw=red!80},    % Change red shade
}
```

### Change Font

Add to preamble:
```latex
\usepackage{fontspec}
\setmainfont{Times New Roman}
\setsansfont{Arial}
```

### Change Figure Size

Modify `width` and `height` in `\pgfplotsset`:
```latex
pgfplotsset{
    width=12cm,
    height=8cm,
}
```

## Troubleshooting

### "Font not found" error
```bash
# Update font cache (macOS)
sudo fc-cache -f -v
```

### "Package not found" error
```bash
# Install missing package (Ubuntu)
sudo apt install texlive-pictures

# Or use tlmgr (MacTeX)
sudo tlmgr install pgfplots
```

### "Dimension too large" error
Reduce figure dimensions or increase compilation memory:
```bash
pdflatex -interaction=nonstopmode -extra-mem-top=10000000 fig_name.tex
```
