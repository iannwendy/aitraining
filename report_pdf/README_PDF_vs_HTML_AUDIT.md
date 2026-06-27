# PDF vs HTML — Audit & Required Fixes

> **File audited:** `523H0002_523H0054_CDNC1_W2.pdf` (136 KB, 9 pages)
> **Reference:** `docs/paper_report.html` (~1,615 lines, full 6-chapter draft)
> **Audit date:** 2026-06-27
> **Audit goal:** Identify every section in the current PDF that must be **rewritten, fixed, expanded, or deleted** to match the HTML ground-truth. The PDF is the Week 2 submission; the HTML is the source-of-truth living document.

---

## 0. Executive Summary

| Severity | Count | Sections affected |
|---|---|---|
| 🔴 Critical (block submission) | 5 | Missing Chapter 3 entirely; missing §2.1 Clinical; abstract numbers stale; 5-vs-6 chapter mismatch |
| 🟠 Major (must fix before review) | 7 | §1.2 missing 7th scope; Limitations missing items; §1.3 outdated chapter map; §II outdated related-work framing; weak-labeler counts stale; affect_signal cross-tab missing |
| 🟡 Minor (polish) | 5 | Reference [29] font glyph bug; "Section 2.2.8" out of place; placeholder headings "III/IV/V"; 11,703 vs 1,786 stale figure |
| 🟢 Cosmetic | 4 | Double-space typo; ">" vs "&rarr;"; inconsistent numbering |

**Headline finding:** The PDF was generated from a **much earlier snapshot** of the project (pre-round-3 review, pre-BERTopic 456/48.30% verification). The HTML has since been updated with corrected numbers and substantially restructured Ch 1–2. The PDF must be **rebuilt from the HTML** before submission.

---

## 1. Title Page & Front Matter

> *(Title-page placeholder fields — author names, affiliations, emails, dates — are intentional template scaffolding and out of scope for this audit. The author block is to be finalized by the team.)*

---

## 2. Abstract (🔴 Critical)

### 2.1. Missing Quantitative Results

**Current PDF abstract** (page 1, ¶3) describes the pipeline but reports **zero performance numbers**:
> "Results demonstrate that PhoBERT achieves…" ← *this sentence is absent*

**HTML abstract** (line 162) reports the headline benchmark:
> "Results demonstrate that PhoBERT achieves an F1-macro of **0.9623** on the in-domain test set and **0.4318** on the cross-domain VSMEC test set, outperforming TF-IDF + SVM (0.9312 / 0.4286), BiLSTM (0.8951 / 0.4272), and BERTopic-only (0.5599 / 0.5030). A critical finding is the substantial generalization gap of approximately 0.53 F1…"

**Required action:** Insert the missing results paragraph into the PDF abstract. Note that the HTML abstract numbers are themselves stale (0.9623, 0.4318, 0.9312 — these are the pre-round-3 figures that **§5.1 explicitly supersedes**). Either:
- (a) Use the **post-round-3 numbers from §5.1** (Table 5.1: PhoBERT in-domain F1-macro = 0.8681 ± 0.0086, cross-domain = 0.3727 ± 0.0242), or
- (b) Update §5.1 to match the abstract numbers if the higher figures are correct.

The abstract and §5.1 must be **internally consistent**.

---

## 3. §1.2 Project Objectives

### 3.1. §1.2 Numbering Mismatch (🟠 Major)

**Current PDF:**
- 1.2.1. Primary Objectives
- 1.2.2. Specific Objectives
- 1.2.3. Expected Results
- 1.2.4. Scope and Limitations

**HTML:**
- 1.2.1. Overarching Aim
- 1.2.2. Specific Objectives
- 1.2.3. Expected Outcomes
- 1.2.4. Scope and Limitations (7 items, (a)–(g))
- Limitations is a **separate bulleted list** inside §1.2.4, not a top-level §1.2.5

**Required fixes:**
- Either rename "Primary Objectives" → "Overarching Aim" (recommended for academic capstone style) and "Expected Results" → "Expected Outcomes", or vice versa.
- Make sure §1.2.4 contains **both** Scope and Limitations as one section, with Limitations as a sub-bulleted list.

### 3.2. §1.2.2 Specific Objectives — Missing Training-Set Size (🟠 Major)

**Current PDF objective 4:**
> "Train five distinct architectures—TF-IDF + SVM, BiLSTM, PhoBERT, BERTopic-only, and PhoBERT + BERTopic—on the final training set (stratified). Evaluate each model on two independent test sets…"

**HTML objective 4 (line 216):**
> "Train five distinct architectures… on the **final training set (1,786 samples, post round-3 review merge, stratified)**. Evaluate each model on two independent test sets: an in-domain test set from the YouTube distribution **(383 samples)** and a fixed cross-domain test set (VSMEC, **3,084 samples**) that is never exposed during training."

**Required fix:** Add the concrete sample counts to the PDF objective 4 — they are load-bearing for the §3.7.3 split description and must match Table 3.13.

### 3.3. §1.2.4 Scope — Missing "Temporal scope" (🟠 Major)

**Current PDF Scope has 6 bullets:**
1. Platform scope
2. Language scope
3. Comment scope
4. Classification scope
5. Model scope
6. Ethical scope

**HTML Scope has 7 bullets:**
1. Platform scope
2. Language scope
3. Comment type
4. Classification granularity
5. Ethical data handling
6. Model scope
7. **Temporal scope** ← missing in PDF

**Required fix:** Add a 7th bullet "Temporal scope: Data were collected during May–June 2026. The rapid evolution of social media linguistic conventions (emergent slang, shifting discourse patterns) may affect model performance on temporally distant data, a limitation common to all social media-based NLP systems."

### 3.4. §1.2.4 Limitations — Missing 3 Items (🔴 Critical)

**Current PDF Limitations has 6 bullets:**
- Platform limitation
- Language limitation
- Comment limitation
- (no severity item)
- (no LLM exclusion item)
- (no temporal limitation item)
- Privacy / paraphrase item

**HTML Limitations has 7 bullets (lines 1139–1151):**
1. Gold set size (1,607 samples, 163 depression-positive)
2. Class imbalance (1:6 ratio)
3. Single annotator (no inter-annotator Kappa possible)
4. Unresolved domain adaptation
5. Single-platform scope

Wait — re-reading: the HTML has **Scope with 7 items** and **Limitations with 5 items**, all under §1.2.4. The PDF has Scope 6 + Limitations 6, mixed. The required structure from the HTML is:

```
1.2.4. Scope and Limitations
   Scope: (a) Platform, (b) Language, (c) Comment type, (d) Classification,
          (e) Ethical data handling, (f) Model scope, (g) Temporal scope
   Limitations: 1. Gold set size, 2. Class imbalance, 3. Single annotator,
                4. Unresolved domain adaptation, 5. Single-platform scope
```

**Required fix:** Restructure §1.2.4 to match the HTML — 7 scope items, 5 limitation items, with Limitations as a sub-list (not a parallel set of scope bullets).

### 3.5. §1.2.3 Expected Results — Stale Numbers (🟠 Major)

**Current PDF Expected Results:**
- "The VietDepression-125K dataset: 125,329 cleaned Vietnamese YouTube comments with weak labels and a 1,607-sample independently annotated gold subset"
- "The VietText-316K unified corpus: 316,401 Vietnamese texts"

These are still correct in the HTML. But the **benchmark performance bullet** says:
> "A comprehensive benchmark of five model architectures evaluated on two test domains, establishing the first published performance figures for Vietnamese depression detection."

**HTML version (line 229) has the actual numbers:**
> "A comprehensive benchmark of five model architectures on two test domains, establishing the first published performance figures for Vietnamese depression detection—**PhoBERT F1-macro: 0.9623 (in-domain), 0.4318 (cross-domain)**."

**Required fix:** Add the F1 numbers to the PDF bullet (and ensure consistency with §5.1 — see Abstract issue above).

### 3.6. §1.2.3 BERTopic Bullet — Stale Topic Count (🟡 Minor)

**Current PDF:**
> "A BERTopic model trained on the Vietnamese corpus, providing a large-scale thematic map of online mental health discourse."

**HTML (line 230):**
> "A BERTopic model comprising **456 topics (verified against `models/bertopic/bertopic_metrics.json`)** trained on the Vietnamese corpus…"

**Required fix:** Add the topic count and the verification reference. PDF §5.3 currently reports 456 but an earlier draft said 461; the HTML resolves this to 456 (verified).

---

## 4. §1.3 Structure of This Report (🔴 Critical — Chapter Count Wrong)

### 4.1. Wrong Number of Chapters

**Current PDF says "five chapters":**
- 1.3.1. Chapter 1: Introduction
- 1.3.2. Chapter 2: Background and Related Work
- 1.3.3. **Chapter 3: Methodology** ← single chapter covers everything
- 1.3.4. Chapter 4: Results and Discussion
- 1.3.5. Chapter 5: Conclusion and Future Work

**HTML says "six chapters":**
- 1.3.1. Chapter 1: Introduction
- 1.3.2. Chapter 2: Background and Related Work
- 1.3.3. **Chapter 3: Data Acquisition, Processing, and Annotation** ← split out
- 1.3.4. **Chapter 4: Model Training and Evaluation Methodology** ← split out
- 1.3.5. Chapter 5: Results and Discussion
- 1.3.6. Chapter 6: Conclusion and Future Work

**Required fix:** Rename §1.3 to "six chapters" and split §1.3.3 into two sub-sections describing the new Ch 3 and Ch 4 separately. Use the descriptions from HTML lines 269–275.

### 4.2. PDF §1.3.3 Description Has the Right Detail but Wrong Chapter Numbering (🟠 Major)

The **content** of §1.3.3 in the PDF already describes the four phases of methodology (Phase I Data, Phase II Labeling, Phase III Model Training, Phase IV Evaluation) at the right level of detail. Once the chapter count is corrected to six, this paragraph becomes an accurate abstract for the merged Ch 3 + Ch 4 narrative — but **Ch 3 in HTML is much more detailed than this paragraph suggests**. The PDF's Chapter 3 (currently empty) must be replaced with the full HTML §3.1–§3.7.

---

## 5. Chapter 3 is Missing Entirely (🔴 Critical)

The PDF table of contents lists "Chapter 3: Methodology" but the actual **Chapter 3 body** consists of only the heading "III. METHODOLOGY" with no content (page 8, line "III. METHODOLOGY" / "IV. RESULTS AND DISCUSSION" / "V. CONCLUSION AND FUTURE WORK" all on consecutive lines with nothing between them).

**Required action:** Insert the entire HTML §3.1–§3.7 (lines 363–911 in `paper_report.html`) into the PDF as Chapter 3. This is **the most critical missing content** and includes:
- §3.1 Data Acquisition Strategy (4 subsections: platform selection, keyword design, API config, crawler architecture, raw schema — Table 3.1)
- §3.2 Data Preprocessing and Cleaning (4 subsections: text normalization, spam detection, deduplication, length filtering)
- §3.3 External Dataset Integration (4 subsections + Table 3.2 + Table 3.3 + Table 3.4)
- §3.4 Unified Corpus Construction (3 subsections + Table 3.5)
- §3.5 Weak-Labeling (6 subsections + Tables 3.6, 3.7, 3.8, 3.9 — including the scoring formula and the weak-labeler performance audit)
- §3.6 Blind Human Annotation Protocol (5 subsections + Tables 3.10, 3.11 — including the Cohen's Kappa 0.63 / −0.03 finding)
- §3.7 Final Training Dataset Assembly (4 subsections + Tables 3.12, 3.13 — including the 1,786 / 383 / 383 / 3,084 split)

This is ~70% of the project's substantive content and **must be present in any submission**.

---

## 6. §II. Background and Related Work (🔴 Critical — Missing §2.1 and §2.3)

### 6.1. Missing §2.1 Clinical Conceptualization (🔴 Critical)

**Current PDF §II:** jumps directly from the chapter opener to "2.1 Related Works".

**HTML §2.1 (lines 297–304):**
- **2.1. Depression: Clinical Conceptualization and Screening Instruments** — covers DSM-5 criteria (9 symptoms, ≥5 required, ≥2 weeks), PHQ-9 (Kroenke et al., 2001; cutoff ≥10, sensitivity 88%, specificity 88%).

**Required action:** Add §2.1 to the PDF. This is essential academic scaffolding for a depression-detection project — without it, the reader has no clinical ground truth for the labels.

### 6.2. Missing §2.2 NLP Approaches Subsection Structure (🟠 Major)

**Current PDF §2.2 "Foundational Knowledge"** has 8 subsections (2.2.1–2.2.8) listed at the very end of the chapter (pages 7–8), awkwardly tacked on after the references.

**HTML §2.2 (lines 307–323)** has a cleaner three-paradigm framing:
- **Lexicon-based approaches** (LIWC, ANEW, De Choudhury et al. 2013)
- **Traditional machine learning approaches** (CLPsych, eRisk, Coppersmith et al. 2014)
- **Deep learning approaches** (BERT, RoBERTa, MentalBERT, PsychBERT, PhoBERT)

**Required fix:** Replace the PDF's §2.2.1–§2.2.8 list with the three-paradigm framing. Move §2.2 to immediately follow §2.1.

### 6.3. §2.2.8 Vietnamese Language Processing — Out of Place (🟡 Minor)

**Current PDF §2.2.8** is the last subsection of §2.2, listed on page 8 right before "III. METHODOLOGY". This is **logically orphaned** — Vietnamese-specific content should be its own top-level section.

**HTML §2.3 (lines 325–349):** "Vietnamese NLP: Language Models and Available Corpora" — a proper top-level section with:
- Vietnamese linguistic properties paragraph
- **Table 2.1** cataloging the eight external Vietnamese datasets integrated into the project (UIT-VSMEC, NTC-SCV, UIT-VSFC, VN Sentiment Analysis, etc.) with sizes and roles

**Required fix:** Promote the Vietnamese content to §2.3, add Table 2.1.

### 6.4. Missing §2.4 The Gap This Work Addresses (🟠 Major)

**HTML §2.4 (line 351):**
> "To the best of our knowledge, no prior work has (1) constructed a Vietnamese-language depression detection dataset with both weak and human-validated labels; (2) implemented a blind review protocol that quantifies annotator independence through Cohen's Kappa; or (3) conducted a systematic cross-domain evaluation comparing multiple deep learning architectures against a fixed, never-seen-in-training test set drawn from a different data distribution. This project is designed to fill these three gaps."

**Required fix:** Add §2.4 to the PDF after §2.3.

### 6.5. §2.1 Related Works — Outdated Framing (🟠 Major)

**Current PDF §2.1 "Related Works"** (page 5) lists six papers grouped under five bold subheadings ("Depression Detection in Social Media", "Vietnamese NLP", "Domain Adaptation", "Cross-Domain Evaluation", "Large Language Models for Mental Health"). Each entry ends with a one-sentence comparison to "our research".

**Problem:** The comparisons repeatedly describe findings the project **no longer supports**:
- "Our research provides contrasting evidence, showing that **DAPT may not be effective** for small Vietnamese datasets…" — this is contradicted by the §5.5 DAPT counter-experiment, which found a *small in-domain win* post-round-3.
- "Our research contributes to this area by providing systematic cross-domain evaluation between YouTube comments and the VSMEC dataset, revealing a **consistent generalization gap of approximately 0.50–0.53 F1-macro** across different model families" — consistent with HTML, OK.
- "Our research specifically addresses Vietnamese language processing and demonstrates the challenges of domain adaptation in low-resource scenarios with **only 3,576 training samples**" — **stale**: the post-round-3 training set is **1,786 samples**, not 3,576.

**Required fix:** Rewrite each comparison paragraph to reflect the post-round-3 numbers (1,786 samples) and the updated DAPT finding (small in-domain gain, marginal cross-domain loss, neither significant). Specifically:
- Replace "DAPT may not be effective" with "DAPT provides a small but consistent in-domain gain (+0.0122 F1) and a marginal cross-domain loss (−0.0107 F1); neither is statistically significant at α = 0.05 with three seeds".
- Replace "3,576 training samples" with "1,786 training samples (post round-3 review merge)".

### 6.6. Missing Citations (🟠 Major)

The HTML References list has 30 entries; the PDF References list has 30 entries but **§2.1 of the PDF cites several works that are not in the References**:
- Zhou et al. (2024) — not in PDF References
- Kumar et al. (2024) — not in PDF References
- Mishra et al. (2024) — not in PDF References
- García-Díaz et al. (2024) — not in PDF References
- Nguyen & Nguyen (2020) — present (entry [16])
- Le et al. (2023) — not in PDF References
- Gururangan et al. (2020) — not in PDF References
- Kenton & Toutanova (2019) — not in PDF References (and the name is "Devlin" — should be Devlin et al. 2019, entry [6])
- Wang et al. (2021) — not in PDF References
- Li et al. (2023) — not in PDF References
- Rahman et al. (2024) — not in PDF References
- Thompson et al. (2024) — not in PDF References

**Required fix:** Either add 10 missing reference entries to the PDF References, or remove the uncited works from §2.1 Related Works.

---

## 7. §III Methodology / §IV Results / §V Conclusion — Placeholders (🟡 Minor)

The PDF has section headings "III. METHODOLOGY", "IV. RESULTS AND DISCUSSION", "V. CONCLUSION AND FUTURE WORK" with **no body content** on page 8. These should be:
- **III** → delete (Chapter 3 "Data Acquisition, Processing, and Annotation" goes here)
- **IV** → delete (Chapter 4 "Model Training and Evaluation Methodology" goes here)
- **V** → delete (Chapter 5 "Results and Discussion" goes here)
- **VI** → add (Chapter 6 "Conclusion and Future Work" goes here)

OR — keep the numbering as in HTML's "six chapters":
- Chapter 3 = Data (inserted from HTML §3)
- Chapter 4 = Model Training Methodology (inserted from HTML §4)
- Chapter 5 = Results (inserted from HTML §5)
- Chapter 6 = Conclusion (inserted from HTML §6)

**Required fix:** Replace the three placeholder headings with the corresponding HTML content (§3.1–§3.7, §4.1–§4.3, §5.1–§5.5, §6.1–§6.3).

---

## 8. References Section

### 8.1. Reference [29] Font Glyph Bug (🟡 Minor)

**Current PDF [29]:**
> "[29] **Bọ Y tế** Việt Nam [Vietnam Ministry of Health]. (2022). Báo cáo **Tỏng quan vè** Sức khỏe Tâm thần tại Việt Nam [Overview Report on Mental Health in Vietnam]."

**HTML [29] (line 1211):**
> "[29] **Bộ Y tế** Việt Nam [Vietnam Ministry of Health]. (2022). Báo cáo **Tổng quan về** Sức khỏe Tâm thần tại Việt Nam [Overview Report on Mental Health in Vietnam]."

**Required fix:** Replace three malformed glyphs:
- `Bọ` → `Bộ` (ô instead of ọ)
- `Tỏng` → `Tổng` (ổ instead of ỏ)
- `vè` → `về` (ề instead of è)

These are font-encoding errors where the combining diacritic was rendered with the wrong base character.

### 8.2. Missing Reference Entries (🟠 Major)

Already covered in §6.6 above. PDF is missing ~10 references that are cited in §2.1.

---

## 9. Body Content Stale Numbers (Consolidated)

The following numbers appear in both the PDF abstract/§1.2 and the HTML §5 but **differ between versions**:

| Quantity | PDF value | HTML value | Source of truth |
|---|---|---|---|
| TF-IDF+SVM in-domain F1 | 0.9312 (from PDF abstract, if present; or older draft) | 0.8286 ± 0.0086 (post round-3, Table 5.1) | `phase3_comparison_report.json` |
| PhoBERT in-domain F1 | 0.9623 (from older draft) | 0.8681 ± 0.0086 (Table 5.1) | `phase3_comparison_report.json` |
| PhoBERT cross-domain F1 | 0.4318 (older draft) | 0.3727 ± 0.0242 (Table 5.1) | `phase3_comparison_report.json` |
| BERTopic-only cross-domain F1-dep | 0.5030 (older) | 0.5566 (Table 5.1) | `phase3_comparison_report.json` |
| Training set size | "stratified" (no number) | 1,786 samples (post round-3) | `phase2_report.json` |
| In-domain test set size | not stated | 383 samples (post round-3) | `phase2_report.json` |
| Cross-domain test set size | 3,084 samples (consistent) | 3,084 samples (consistent) | OK |
| Training samples pre-Phase-1 | 3,576 (from §2.1) | 2,632 (from DAPT erratum, §5.5) | `tests/test_dapt_eval_helpers.py` |
| BERTopic topic count | not stated | 456 (verified, §5.3) | `models/bertopic/bertopic_metrics.json` |
| BERTopic outlier rate | not stated | 48.30% (verified, §5.3) | `models/bertopic/bertopic_metrics.json` |
| DAPT effect | "not effective" | "small in-domain gain, marginal cross-domain loss" | `results/domain_adapted_eval_2026-06-26_181310/` |

**Required fix:** Reconcile all numbers across abstract, §1.2, §2.1, §5.1, §5.5 to use the **post-round-3 verified numbers**.

---

## 10. Cosmetic Issues (🟢)

| # | Location | Current | Should be |
|---|---|---|---|
| 1 | Page 1, line 3 | "DETECTION OF DEPRESSION SIGNS IN VIETNAMESE…" (all caps via LaTeX `\uppercase`) | Title-case, sentence-case per HTML |
| 2 | §2.1 entries | Use of `→` arrows for "differs from our work" comparisons | Consider reformulating as tables or footnotes |
| 3 | §1.2 bullets | Mix of numbered lists (1, 2, 3) and bullets (•) | Use consistent format — HTML uses `<ol>` everywhere |
| 4 | References | "[NGUYEN DUC ANH]" bracketed all-caps | Sentence case |

---

## 11. Action Plan (Priority Order)

To get the PDF to a submission-ready state, perform the following in order:

1. **[🔴 Critical]** Insert full Chapter 3 (HTML §3.1–§3.7) into the PDF body — this is the bulk of the missing content.
2. **[🔴 Critical]** Insert quantitative results paragraph into the abstract (and reconcile with §5.1).
3. **[🔴 Critical]** Add §2.1 Clinical Conceptualization, §2.4 Gap Statement, and 10 missing references.
4. **[🟠 Major]** Restructure §1.2.4 Scope (7 items) and add §1.2.4 Limitations (5 items, sub-list).
5. **[🟠 Major]** Rename §1.3 to "six chapters" and split §1.3.3.
6. **[🟠 Major]** Reconcile all stale numbers across abstract / §1.2 / §2.1 / §5.1 / §5.5 to post-round-3 values.
7. **[🟠 Major]** Add Table 2.1 (external Vietnamese corpora catalog) to §2.3.
8. **[🟠 Major]** Insert Chapters 4, 5, 6 (HTML §4, §5, §6) — currently placeholder-only in PDF.
9. **[🟡 Minor]** Fix Reference [29] font glyph bug.
10. **[🟢 Cosmetic]** Polish formatting, remove placeholder brackets, ensure consistent casing.

**Recommended approach:** Rather than patching the PDF incrementally, **regenerate the PDF from the HTML source** (e.g., via headless Chrome print or a PDF build script). The HTML is already well-structured and consistent — manually porting will reintroduce errors.

---

## 12. Files Referenced

- PDF source: `report_pdf/523H0002_523H0054_CDNC1_W2.pdf`
- HTML source: `docs/paper_report.html` (1,615 lines)
- BERTopic metrics: `models/bertopic/bertopic_metrics.json`
- DAPT results (current): `results/domain_adapted_eval_2026-06-26_181310/`
- DAPT results (superseded): `results/domain_adapted_eval_2026-06-25_123440/`
- Phase 2 final dataset: `phase2_report.json`
- Phase 3 comparison: `phase3_comparison_report.json`
- DAPT regression test: `tests/test_dapt_eval_helpers.py` (`TestRunFinetuneDataPath`)
- Label Studio batches: `label_studio_step5_review_key_MERGED.csv`, `label_studio_step8_active_learning_key_MERGED.csv`, `label_studio_round3_active_learning_key_MERGED.csv`

---

*End of audit. Last updated 2026-06-27.*
