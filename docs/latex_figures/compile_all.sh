#!/bin/bash
# compile_all.sh - Compile all LaTeX figures to PDF and PNG
# Usage: ./compile_all.sh [output_format]
#   output_format: pdf (default), png, or both

OUTPUT_FORMAT=${1:-both}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create output directories
mkdir -p pdf png

# List of all figure files
FIGURES=(
    "fig_c1_framework"
    "fig_c2_taxonomy"
    "fig_c4_pipeline"
    "fig3_1_weak_label"
    "fig5_1_generalization_gap"
    "fig5_2_bertopic_topics"
    "fig5_3_confusion_matrices"
    "fig5_4_dapt_experiment"
    "fig_augmentation"
)

echo "=========================================="
echo "LaTeX Figure Compilation"
echo "=========================================="
echo "Output format: $OUTPUT_FORMAT"
echo "Working directory: $SCRIPT_DIR"
echo ""

# Check for pdflatex
if ! command -v pdflatex &> /dev/null; then
    echo "ERROR: pdflatex not found!"
    echo ""
    echo "Please install MacTeX:"
    echo "  brew install --cask mactex-no-gui"
    echo ""
    echo "Or use Homebrew:"
    echo "  brew install mactex"
    echo ""
    echo "After installation, run this script again."
    exit 1
fi

# Function to compile a single figure
compile_figure() {
    local fig_name="$1"
    local fig_file="${fig_name}.tex"
    local base_name=$(basename "$fig_name")

    if [ ! -f "$fig_file" ]; then
        echo "  [SKIP] $fig_file not found"
        return 1
    fi

    echo "  Compiling $fig_file..."

    # Compile with pdflatex
    pdflatex -interaction=nonstopmode \
        -halt-on-error \
        -output-directory=pdf \
        "$fig_file" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "    [OK] $base_name.pdf created"

        # Convert to PNG if requested
        if [ "$OUTPUT_FORMAT" = "png" ] || [ "$OUTPUT_FORMAT" = "both" ]; then
            if command -v convert &> /dev/null; then
                convert -density 300 "pdf/${base_name}.pdf" -quality 100 "png/${base_name}.png"
                echo "    [OK] $base_name.png created"
            else
                echo "    [SKIP] ImageMagick not installed (no PNG conversion)"
            fi
        fi
    else
        echo "    [FAIL] $base_name failed to compile"
        return 1
    fi
}

# Main compilation loop
echo "Compiling figures..."
echo ""
for fig in "${FIGURES[@]}"; do
    compile_figure "$fig"
done

echo ""
echo "=========================================="
echo "Compilation complete!"
echo ""

if [ "$OUTPUT_FORMAT" = "both" ] || [ "$OUTPUT_FORMAT" = "png" ]; then
    echo "Output files:"
    echo "  PDF: $SCRIPT_DIR/pdf/"
    echo "  PNG: $SCRIPT_DIR/png/"
else
    echo "Output files:"
    echo "  PDF: $SCRIPT_DIR/pdf/"
fi
echo "=========================================="
