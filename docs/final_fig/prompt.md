# Prompts for Generating Academic Diagrams

Use these prompts with ChatGPT (with image generation like DALL-E/GPT-4V) or Claude to generate professional academic diagrams.

---

## Figure 1: Conceptual Framework (Three-Layer Diagram)

**Prompt:**
```
Create a professional academic diagram showing a THREE-LAYER CONCEPTUAL FRAMEWORK for detecting depression signs in Vietnamese social media.

The diagram should have 4 horizontal layers arranged vertically with connecting arrows:

LAYER 1 - CLINICAL REALITY (top, color: vermillion #E34234):
- Box 1: "MDD (DSM-5)"
- Box 2: "Stigma, Workforce"  
- Box 3: "PHQ-9 Self-Report"

↓ (arrow labeled "0.2 psychiatrists")

LAYER 2 - SOCIAL MEDIA (color: blue #3B82F6):
- Box 1: "125,329 YouTube Comments"
- Box 2: "Linguistic Behavior"

↓ (arrow)

LAYER 3 - ML PIPELINE (color: green #22C55E):
- Box 1: "Weak Label" → Box 2: "Annotation" → Box 3: "PhoBERT"

↓ (arrow labeled "Round 5")

EVALUATION (bottom, color: orange #F97316):
- Left box: "In-domain (n=912)"
- Middle: "ΔF1 ≈ 0.37"
- Right box: "Cross-domain (n=3,084)"

Style requirements:
- Clean, professional academic look
- White background
- Rounded rectangle boxes with light fill and darker border
- Clear hierarchy with labels for each layer
- Font: sans-serif, readable
- Include a legend or key
- Output as high-resolution PNG or PDF
```

---

## Figure 2: NLP Taxonomy Tree

**Prompt:**
```
Create a professional METHODOLOGICAL TAXONOMY tree diagram for NLP approaches to depression detection.

Structure (hierarchical tree from top to bottom):

ROOT: "NLP Approaches"

BRANCH 1 - Lexicon-based (gray):
├── Context-blind
└── Language-specific

BRANCH 2 - Traditional ML (blue):
├── Feature Engineering
└── Shallow Semantics

BRANCH 3 - Deep Learning (blue, lighter):
├── Generic BERT
│   └── MentalBERT
└── ★ PhoBERT (This) [HIGHLIGHTED with green border]

Color scheme:
- Root: gray
- Lexicon-based: gray #9CA3AF
- Traditional ML: blue #3B82F6
- Deep Learning: lighter blue
- PhoBERT (highlighted): green #22C55E with thick border

Add a legend box in bottom-left corner with:
- "Round 5 Results:"
- "PhoBERT F1: 0.8596 (in-domain)"
- "Cross-domain: 0.4937"
- "Dataset: 6,080 samples"

Style: Professional academic tree diagram, white background, clean typography
```

---

## Figure 3: Pipeline Overview (15-Step Flowchart)

**Prompt:**
```
Create a professional PIPELINE OVERVIEW flowchart showing a 15-step ML pipeline for depression detection.

Structure with TWO MAIN SECTIONS separated by a vertical line on the left:

SECTION 1 - "Chapter 3" (blue theme #3B82F6):
Row 1 (left to right): 
[1. Crawl] → [2. Clean] → [3. External] → [4. Corpus]
Row 2 (below):
[5. Weak Label] → [6. Annotate] → [7. Gold Set]

SECTION 2 - "Chapter 4" (green theme #22C55E):
[11. Final Dataset (6,080)] → [12-13. Train Models] → [14. In-domain (n=912)] & [15. Cross-domain (n=3,084)]

Arrow connecting Chapter 3 to Chapter 4 labeled "15-step pipeline"

Box styles:
- Regular steps: light fill with colored border
- Highlighted steps (14, 15): orange border #F97316, thicker border

Style: Clean flowchart, white background, professional academic look, clear section labels
```

---

## Figure 4: Weak-Label Distribution (Bar Chart)

**Prompt:**
```
Create a professional BAR CHART showing weak-label category distribution.

Data to plot:
- depression_auto: 2.57% (n=3,223) - RED #E34234
- uncertain: 78.52% (n=98,410) - GRAY #9CA3AF
- normal_auto: 18.91% (n=23,695) - BLUE #3B82F6
- need_review: 96.01% (n=120,334) - ORANGE #F97316

Chart specifications:
- Y-axis: "Percentage (% of 125,329)" (0-100%)
- X-axis: Weak Label Category
- Add data labels on top of each bar showing percentage and count
- Grid lines for readability
- Legend or color key

Style: Clean academic bar chart, white background, professional typography
```

---

## Figure 5: Generalization Gap (Grouped Bar Chart)

**Prompt:**
```
Create a professional GROUPED BAR CHART comparing model performance.

Data (5 model groups, each with 2 bars):

Models (X-axis):
1. PhoBERT (avg vote)
2. TF-IDF + LinearSVC
3. TF-IDF + LogReg
4. BiLSTM
5. PhoBERT + BERTopic

In-domain values (BLUE #3B82F6):
0.8596, 0.8629, 0.8504, 0.8049, 0.7868

Cross-domain values (RED #EF4444):
0.4937, 0.4129, 0.4504, 0.4549, 0.4501

Chart specifications:
- Y-axis: "F1-macro" (0.0 - 1.0)
- Legend: "In-domain (n=912)" and "Cross-domain (n=3,084)"
- Add delta (Δ) annotations above each group showing the generalization gap
- Grid lines for readability

Style: Clean academic grouped bar chart, white background, professional typography
```

---

## Figure 6: BERTopic Topic Distribution

**Prompt:**
```
Create a professional BAR CHART showing BERTopic topic distribution (Top 10).

Data:
- Topic 1 (Outlier): 149,650 documents - GRAY #9CA3AF
- Topic 2: 1,687 - RED (depression-related) #E34234
- Topic 3: 1,214 - RED
- Topic 4: 1,052 - RED
- Topic 5: 844 - RED
- Topic 6: 749 - RED
- Topic 7: 1,800 - BLUE (other) #3B82F6
- Topic 8: 1,600 - BLUE
- Topic 9: 1,400 - BLUE
- Topic 10: 1,200 - BLUE

Chart specifications:
- X-axis: "Topic ID (Top 10)"
- Y-axis: "Document Count"
- Legend showing: "Depression Topic" (red), "Outlier" (gray), "Other" (blue)
- Add annotation box with:
  - "Key Topics:"
  - "Topic 7: Sleep, medicine"
  - "Topic 14: Sadness, music"
  - "Topic 19: Burnout, work"
  - "Topic 27: Loneliness"
  - "Topic 33: Clinical depression"
  - "Outlier: 149,650 (48.3%)"

Style: Clean academic bar chart, white background
```

---

## Figure 7: Confusion Matrices

**Prompt:**
```
Create TWO SIDE-BY-SIDE CONFUSION MATRICES for a depression detection model.

LEFT MATRIX - In-domain (n=912):
- True Negative (TN): 342
- False Positive (FP): 89
- False Negative (FN): 52
- True Positive (TP): 429
- Title: "PhoBERT - In-domain (n=912)"

RIGHT MATRIX - Cross-domain (n=3,084):
- True Negative (TN): 1,847
- False Positive (FP): 412
- False Negative (FN): 825
- True Positive (TP): calculate from data
- Title: "PhoBERT - Cross-domain (n=3,084)"

Matrix specifications:
- Use blue color scale (darker = higher values)
- Label rows: "Actual: Non-Depression", "Actual: Depression"
- Label columns: "Predicted: Non-Depression", "Predicted: Depression"
- Show both count and percentage in each cell
- Add colorbar legend

Bottom note: "TN = True Negative, TP = True Positive, FN = False Negative, FP = False Positive"

Style: Clean heatmap/confusion matrix, white background, professional academic
```

---

## Figure 8: DAPT Experiment Results

**Prompt:**
```
Create a professional GROUPED BAR CHART for DAPT (Domain-Adaptive Pre-Training) counter-experiment results.

Data (4 groups):

Group 1: In-domain Original - 0.8681 (BLUE #3B82F6)
Group 2: In-domain + DAPT - 0.8803 (RED #EF4444)
Group 3: Cross-domain Original - 0.3727 (BLUE)
Group 4: Cross-domain + DAPT - 0.3620 (RED)

Chart specifications:
- Y-axis: "F1-macro" (0.0 - 1.0)
- Title: "DAPT Counter-Experiment"
- Legend: "PhoBERT (Original)" and "PhoBERT + DAPT"
- Add annotations:
  - Δ=-0.012 above In-domain groups
  - "(n.s.)" indicating not significant
  - Δ=+0.011 above Cross-domain groups
- Grid lines for readability

Style: Clean academic grouped bar chart, white background
```

---

## Figure 9: Data Augmentation Results

**Prompt:**
```
Create a professional GROUPED BAR CHART showing data augmentation experiment results.

Data (3 groups, 4 bars each):

Models:
1. PhoBERT
2. BERTopic-only
3. PhoBERT + BERTopic

Values:
- In-domain (before): 0.8681, 0.5599, 0.8504 - Light BLUE
- In-domain (after): 0.9619, 0.5864, 0.9377 - Dark BLUE
- Cross-domain (before): 0.3727, 0.5030, 0.3977 - Light RED
- Cross-domain (after): 0.3993, 0.5022, 0.5262 - Dark RED

Chart specifications:
- Y-axis: "F1-macro" (0.0 - 1.1)
- Legend: 4 items "In (before)", "In (after)", "Cross (before)", "Cross (after)"
- Add improvement annotations:
  - "+9.38%" above first group (PhoBERT in-domain improvement)
  - "+12.85%" above third group (cross-domain improvement)
- Grid lines for readability

Style: Clean academic grouped bar chart, white background, professional typography
```

---

## General Style Guidelines for All Diagrams

```
Style preferences:
- Format: PNG with transparent or white background, or PDF
- Resolution: High resolution (at least 300 DPI)
- Font: Sans-serif (Helvetica, Arial, or similar)
- Font sizes: Title 14-16pt, Labels 10-12pt, Annotations 8-10pt
- Colors: Use the specified hex codes for consistency
- Layout: Clean, professional, academic style
- NO decorative elements or clip art
- Clear visual hierarchy
- Adequate spacing between elements
- Export as vector format (SVG or PDF) when possible for best quality
```

---

## Alternative: Use with Draw.io / Excalidraw

If you prefer to create these manually:

1. **Draw.io template colors:**
   - Vermillion: #E34234
   - Blue: #3B82F6
   - Green: #22C55E
   - Orange: #F97316
   - Red: #EF4444
   - Gray: #9CA3AF

2. **Standard box style:**
   - Fill: 20% opacity of main color
   - Border: Full color, 1-2pt
   - Corner radius: 3-5pt
   - Padding: adequate for text

3. **Arrow style:**
   - Type: Simple arrow
   - Color: Gray or matching theme color
   - Width: 1-2pt
