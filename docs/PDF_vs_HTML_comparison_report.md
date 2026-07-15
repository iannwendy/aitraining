# BÁO CÁO SO SÁNH: PDF vs HTML
## Detection of Depression Signs in Vietnamese Social Media Text Using Deep Learning Models

**Ngày tạo:** 2026-07-15  
**Tác giả:** Claude Code  
**Mục đích:** So sánh chi tiết các số liệu và nội dung giữa file PDF (bản cũ, tháng 6/2026) và file HTML (bản mới, 2026)

---

## 1. TỔNG QUAN

### 1.1. Thông tin Tác giả và Trường học

| Thành phần | PDF (Bản cũ) | HTML (Bản mới) | Cần sửa? |
|------------|---------------|-----------------|----------|
| **Tên tác giả** | NGUYEN DUC ANH¹, NGUYEN BAO MINH² (2 tác giả) | Bao Minh Nguyen (1 tác giả) | ✅ CẦN SỬA |
| **Student ID** | 523H0002, 523H0054 | 523H0054 | ✅ CẦN SỬA |
| **Email** | 523h0002@student.tdtu.edu.vn, 523h0054@student.tdtu.edu.vn | 523h0054@student.hcmiu.edu.vn | ✅ CẦN SỬA |
| **Trường** | Ton Duc Thang University | University of Information Technology, VNU-HCM | ✅ CẦN SỬA |
| **Khoa** | Faculty of Information Technology | Department of Computer Science | ✅ CẦN SỬA |
| **Khóa** | Academic Year 2025–2026 | Academic Year 2025–2026 | ✅ Giữ nguyên |

---

## 2. SỐ LIỆU DATASET

### 2.1. Số lượng Keywords

| Thành phần | PDF | HTML | Cần sửa? |
|------------|-----|------|----------|
| **Tổng số keywords** | **265** (line 96: "265 depression-related search keywords") | **264** (Section 1.2.2: "264 Vietnamese-language search keywords") | ✅ CẦN SỬA |

**Câu cần thay đổi (PDF, line 96):**
> "Crawl over 125,000 Vietnamese YouTube comments via the YouTube Data API v3 using **265** depression-related search keywords"

**Thay đổi thành (HTML):**
> "Crawl over 125,000 Vietnamese YouTube comments via the YouTube Data API v3 using **264** Vietnamese-language search keywords"

### 2.2. Số lượng Mẫu trong Dataset

| Dataset | PDF | HTML | Cần sửa? |
|---------|-----|------|----------|
| **Final Dataset** | 1,786 samples (Section 1.2.3, Table 13, Table 15) | **6,080 samples** (Table 5.1, Abstract) | ✅ CẦN SỬA |
| **Training rows** | 1,786 (70%) | 4,256 training rows | ✅ CẦN SỬA |
| **In-domain Test** | 383 samples | **912 samples** (line 1024) | ✅ CẦN SỬA |
| **Newly annotated samples** | Không có | **1,533 newly annotated** | ✅ CẦN THÊM |
| **Gold set** | 1,607 samples | 1,607 samples | ✅ Giữ nguyên |
| **Unified corpus** | 316,401 | 316,401 | ✅ Giữ nguyên |
| **YouTube comments** | 125,329 | 125,329 | ✅ Giữ nguyên |
| **External datasets** | 191,072 | 191,072 | ✅ Giữ nguyên |
| **VSMEC test set** | 3,084 | 3,084 | ✅ Giữ nguyên |

---

## 3. KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH (QUAN TRỌNG NHẤT)

### 3.1. Round 4 Dataset Results (CÓ TRONG HTML, KHÔNG CÓ TRONG PDF)

HTML Section 5.1 có kết quả **Post Round 4 Dataset (6,079 samples)** - KHÔNG TỒN TẠI trong PDF:

| Model | In-domain F1-macro | Cross-domain F1-macro | F1-depression (in) | Ghi chú |
|-------|-------------------|----------------------|-------------------|---------|
| PhoBERT (Round 4) | 0.8417 ± 0.0220 | 0.3850 ± 0.0219 | 0.7359 ± 0.0385 | ❌ KHÔNG CÓ TRONG PDF |

**Cần thêm vào PDF:**
Thêm section "Post Round 4 Dataset (6,079 samples)" vào bảng kết quả với các giá trị trên.

### 3.2. Round 5 Dataset Results (CHỈ CÓ TRONG HTML)

**ĐÂY LÀ SỐ LIỆU MỚI NHẤT - KHÔNG TỒN TẠI TRONG PDF:**

#### 3.2.1. Final Results (Post Round 5 Dataset - 6,080 samples)

| Model | Acc (in) | Prec-M (in) | Rec-M (in) | **F1-M (in)** | F1-W (in) | F1-Dep (in) | **F1-M (cross)** | Acc (cross) |
|-------|----------|-------------|------------|---------------|-----------|-------------|-----------------|-------------|
| **PhoBERT (avg vote, 3 seeds)** | 0.9178 | 0.8490 | 0.8715 | **0.8596** | 0.9191 | 0.7692 | **0.4937** | 0.5772 |
| TF-IDF + LinearSVC | 0.9211 | 0.8576 | 0.8684 | 0.8629 | **0.9216** | **0.7736** | — | — |
| TF-IDF + LogReg | 0.9046 | 0.8206 | 0.8967 | 0.8504 | 0.9096 | 0.7603 | — | — |
| BiLSTM (random, avg) | 0.8984 | — | — | 0.8049 | — | — | — | — |
| PhoBERT + BERTopic | 0.8739 | — | — | 0.7868 | — | 0.6505 | 0.4501 | 0.5454 |

**Ghi chú quan trọng:**
- Cross-domain F1 improved from **0.3727 (pre-Round 4)** to **0.4937 (Round 5, +0.1210)**
- PhoBERT cross-domain improvement +0.1210 demonstrates active learning significantly improves generalization
- Generalization gap reduced from **0.4954** to **0.3661**

#### 3.2.2. Abstract Updates (HTML)

**Câu cần thay đổi (PDF Abstract, line 31-34):**
> "The strongest model, PhoBERT, reached an F1-macro of **0.8681±0.0086** on our own in-domain test set, but only **0.3727±0.0242** when evaluated on VSMEC"

**Thay đổi thành (HTML Abstract):**
> "Results demonstrate that PhoBERT with majority voting across three seeds achieves an F1-macro of **0.8596** on the in-domain test set (912 samples) and **0.4937** on the cross-domain VSMEC test set (3,084 samples), with a generalization gap of **0.37 F1** (post Round 5 dataset: 6,080 training samples)."

#### 3.2.3. Expected Outcomes Update (HTML Section 1.2.3)

**Câu cần thay đổi (PDF, line 136-137):**
> "first published numbers for Vietnamese depression detection specifically (PhoBERT F1-macro: **0.8681±0.0086** in-domain, **0.3727±0.0242** cross-domain)"

**Thay đổi thành (HTML, line 235):**
> "A comprehensive benchmark of five model architectures on two test domains, establishing the first published performance figures for Vietnamese depression detection—PhoBERT F1-macro: **0.8596** (in-domain), **0.4937** (cross-domain)"

#### 3.2.4. Section 5.1 Text Updates

**Câu cần thay đổi (PDF, line 1722-1726):**
> "On the post-round-4 dataset (6,079 samples, 4,255 training rows), the in-domain ranking runs roughly TF-IDF + LinearSVC (0.8799) ≈ PhoBERT (0.8417 ± 0.0220) > TF-IDF + LogReg (0.8415)..."

**Thay đổi thành (HTML, line 1046-1047):**
> "First, on the post-round-5 final_dataset (6,080 samples, 4,256 train rows) the in-domain ranking is: PhoBERT avg vote (0.8596 F1) ≈ TF-IDF + LinearSVC (0.8629) > TF-IDF + LogReg (0.8504) > BiLSTM (0.8049). PhoBERT with majority voting across three seeds achieves the best balance of performance metrics. **Notably, PhoBERT's cross-domain performance improved substantially from 0.3727 (pre-Round 4) to 0.4937 (Round 5, +0.1210), demonstrating that active learning significantly improves generalization to the VSMEC domain.**"

### 3.3. Generalization Gap Update

| Thành phần | PDF | HTML | Thay đổi |
|------------|-----|------|----------|
| **PhoBERT (Round 5) ΔF1** | Không có | **0.3661** | ✅ THÊM MỚI |
| **PhoBERT (Round 4) ΔF1** | Không có | 0.4567 | ✅ THÊM MỚI |
| **PhoBERT (pre-R4) ΔF1** | ~0.50 (0.4954) | 0.4954 | Giữ nguyên |

---

## 4. BERTOPIC TOPICS

### 4.1. Số lượng Topics

| Thành phần | PDF | HTML | Cần sửa? |
|------------|-----|------|----------|
| **Số topics** | 456 | 456 | ✅ Giữ nguyên |
| **Outlier rate** | 48.30% | 48.30% | ✅ Giữ nguyên |
| **Source** | models/bertopic/bertopic_metrics.json | models/bertopic/bertopic_metrics.json | ✅ Giữ nguyên |

**Ghi chú:** Cả hai file đều ghi nhận 456 topics và 48.30% outlier rate, đã được verify với models/bertopic/bertopic_metrics.json.

---

## 5. TRAINING DATASET DETAILS

### 5.1. Cross-Domain Improvement Highlight

**Thêm mới vào HTML (không có trong PDF):**

> "Notably, the cross-domain F1 improved substantially from **0.3727 (pre-Round 4)** to **0.4937 (Round 5, +0.1210)** after five rounds of active learning annotation, demonstrating that diverse human-labeled data significantly improves generalization."

---

## 6. CÁC ĐIỂM KHÁC BIỆT VỀ NỘI DUNG

### 6.1. Author Information in Abstract

| PDF (Abstract) | HTML (Abstract) |
|----------------|-----------------|
| Không có tên trong abstract | Không có tên trong abstract |

### 6.2. Training Dataset Section (Section 3.7)

**PDF Section 3.7.3 (line 1466-1477):**
> Table 15: Final dataset split configuration: Train 70% = 1,786, Validation 15% = 383, Test 15% = 383

**HTML Section 3.7.3:**
> Table 13: Final dataset split configuration: Train 70% = 1,786, Validation 15% = 383, Test 15% = 383

→ Giữ nguyên (đây là kết quả trước Round 4/5)

### 6.3. Figure 2 Update (Model Training Pipeline)

**PDF Figure 2 (page 22):**
> Step 11. Build final_dataset.csv (2,553 samples, multi-source, stratified 70/15/15 split, post round-3 review merge)

**HTML Figure 4.1:**
> Step 11. Build final_dataset.csv (2,553 samples, multi-source, stratified 70/15/15 split, post round-3 review merge)

→ Giữ nguyên (đây là pipeline cũ)

---

## 7. SỐ LIỆU AUGMENTATION (SECTION 5.6)

### 7.1. Augmented Results Table

Cả hai file đều có Table 19/5.4 nhưng số liệu đã được cập nhật:

| Model | Before (in) | After (in) | ΔIn | Before (cross) | After (cross) | ΔCross |
|-------|-------------|------------|-----|----------------|---------------|--------|
| PhoBERT | 0.8681 | **0.9619** | +0.0938 | 0.3727 | **0.3993** | +0.0266 |
| BERTopic-only | 0.5599 | 0.5864 | +0.0265 | 0.5030 | 0.5022 | -0.0008 |
| PhoBERT + BERTopic | 0.9501 | 0.9377 | -0.0124 | 0.3977 | **0.5262** | +0.1285 |

---

## 8. DANH SÁCH CÁC THAY ĐỔI CẦN THỰC HIỆN

### 8.1. Thông tin Tác giả (PDF → HTML)

1. **Xóa:** NGUYEN DUC ANH¹, Student ID 523H0002, Email 523h0002@student.tdtu.edu.vn
2. **Giữ lại:** Bao Minh Nguyen, Student ID 523H0054, Email 523h0054@student.hcmiu.edu.vn
3. **Đổi trường:** Ton Duc Thang University → University of Information Technology, VNU-HCM
4. **Đổi khoa:** Faculty of Information Technology → Department of Computer Science

### 8.2. Số liệu Keywords

1. **Sửa:** "265 depression-related search keywords" → "264 Vietnamese-language search keywords"

### 8.3. Dataset Sizes

1. **Thêm mới:** Round 4 Dataset (6,079 samples) với kết quả PhoBERT: 0.8417/0.3850
2. **Thêm mới:** Round 5 Dataset (6,080 samples) với kết quả PhoBERT (avg vote): 0.8596/0.4937
3. **Thêm mới:** Cross-domain F1 improvement: 0.3727 → 0.4937 (+0.1210)
4. **Thêm mới:** Generalization gap: 0.4954 → 0.3661

### 8.4. Abstract Updates

1. **Sửa toàn bộ** phần kết quả PhoBERT trong Abstract từ "0.8681±0.0086 in-domain, 0.3727±0.0242 cross-domain" → "0.8596 in-domain, 0.4937 cross-domain, generalization gap of 0.37 F1 (post Round 5 dataset: 6,080 training samples)"

### 8.5. Section 5.1 Results

1. **Thêm mới:** Section "Post Round 4 Dataset (6,079 samples)" vào bảng kết quả
2. **Thêm mới:** Section "Post Round 5 Dataset (6,080 samples, 1,533 newly annotated) — FINAL RESULTS" vào bảng kết quả
3. **Thêm mới:** PhoBERT (avg vote, 3 seeds) với các chỉ số đầy đủ
4. **Thêm mới:** TF-IDF + LinearSVC, TF-IDF + LogReg, BiLSTM, PhoBERT + BERTopic với Round 5 results

### 8.6. Section 1.2.3 Expected Outcomes

1. **Sửa:** PhoBERT F1-macro: "0.8681 ± 0.0086 (in-domain), 0.3727 ± 0.0242 (cross-domain)" → "0.8596 (in-domain), 0.4937 (cross-domain)"

---

## 9. TÓM TẮT

### 9.1. Các thay đổi lớn

| STT | Loại thay đổi | Chi tiết | Mức độ |
|-----|---------------|----------|--------|
| 1 | Thông tin tác giả | Từ 2 tác giả → 1 tác giả, đổi trường | ⚠️ Rất quan trọng |
| 2 | Số keywords | 265 → 264 | ⚠️ Quan trọng |
| 3 | Round 4/5 results | Thêm hoàn toàn mới | 🔴 Quan trọng nhất |
| 4 | Dataset size | 1,786 → 6,080 samples | ⚠️ Rất quan trọng |
| 5 | Final PhoBERT F1 | 0.8681/0.3727 → 0.8596/0.4937 | 🔴 Quan trọng |
| 6 | Generalization gap | 0.4954 → 0.3661 | 🔴 Quan trọng |

### 9.2. Khuyến nghị

1. **PDF đã LỖI THỜI** - Cần cập nhật toàn bộ phần kết quả (Section 5.1)
2. **Thông tin tác giả** trong PDF không còn chính xác - Cần xóa thông tin tác giả thứ 2
3. **Số liệu dataset** trong PDF cần cập nhật từ 1,786 → 6,080 samples
4. **Phần quan trọng nhất** cần thêm vào PDF là Round 5 results với PhoBERT (avg vote, 3 seeds): 0.8596/0.4937

---

## 10. BẢNG SO SÁNH CHI TIẾT CÁC SỐ LIỆU

### 10.1. PhoBERT Performance Comparison

| Version | In-domain F1 | Cross-domain F1 | Gap | Dataset Size |
|---------|--------------|-----------------|-----|--------------|
| **PDF (Pre-Round 4)** | 0.8681 ± 0.0086 | 0.3727 ± 0.0242 | 0.4954 | 1,786 |
| **HTML (Round 4)** | 0.8417 ± 0.0220 | 0.3850 ± 0.0219 | 0.4567 | 6,079 |
| **HTML (Round 5)** | 0.8596 | 0.4937 | 0.3661 | 6,080 |

### 10.2. Cross-Domain F1 Improvement

| Rounds | Before | After | Improvement |
|--------|--------|-------|-------------|
| Pre-R4 → R4 | 0.3727 | 0.3850 | +0.0123 |
| R4 → R5 | 0.3850 | 0.4937 | **+0.1087** |
| Pre-R4 → R5 | 0.3727 | 0.4937 | **+0.1210** |

---

*Báo cáo này được tạo bởi Claude Code vào ngày 2026-07-15*
