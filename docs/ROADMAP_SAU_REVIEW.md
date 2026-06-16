# Roadmap sau khi review thủ công xong

Tài liệu này vạch sẵn các bước **sau khi thành viên review trả về 2 file export từ Label Studio**
(đợt 8 active-learning + đợt 5 review). Mục tiêu: đi từ nhãn người-gán → `final_dataset.csv`
→ train dãy model so sánh → báo cáo. Bám đúng bước 9-15 trong pipeline của nhóm.

> Bối cảnh quan trọng đã phát hiện trong quá trình làm:
> - Recall của keyword weak-labeler trên distress người-gán chỉ **0.91%** → keyword mù với câu buồn ngắn.
> - Gold cũ cho baseline **accuracy 1.0 ảo** vì người review chấp nhận lại gợi ý hệ thống (96.3% trùng).
> - Vì vậy file review lần này là **blind** (chỉ `row_id` + `text`), buộc người gán độc lập.
> - Cross-domain test (VSMEC 3.084 dòng): baseline F1 **0.61**, PhoBERT-lần-1 F1 **0.76** — đây là điểm trung thực, không phải 1.0.

---

## Đầu vào khi bắt đầu roadmap

Thành viên review trả về:
- `label_studio_step8_active_learning_export.csv` (1.000 dòng, ưu tiên đợt 1)
- `label_studio_step5_review_export.csv` (750 dòng, đợt 2)

Mỗi dòng có `row_id` + nhãn người chọn (`depression` / `normal` / `uncertain` / `exclude`).
Hệ thống đã giữ sẵn `docs/*_key.csv` để ghép nhãn về dữ liệu gốc qua `row_id`.

---

## Phase 1 — Ghép nhãn & khôi phục gold SẠCH (mở khóa lại bước 5)

1. **Merge** export ↔ key qua `row_id` → ghép `final_label` người-gán về `review_samples.csv`
   và `phobert_active_learning_samples.csv`.
2. **Kiểm định chất lượng review** (để chứng minh không lặp lỗi cũ):
   - Đo **tỷ lệ bất đồng người vs máy**. Vì lần này blind nên PHẢI có bất đồng đáng kể;
     nếu vẫn ~96% trùng → review chưa độc lập, báo lại ngay trước khi đi tiếp.
   - Nếu ≥2 người cùng review một phần → tính **Cohen's kappa** (chỉ số nhóm cần cho báo cáo).
   - Thống kê tỷ lệ `uncertain` / `exclude`.
3. **Rebuild gold** (`gold_builder`) → `gold_review.csv` mới → **chạy lại** đánh giá weak-label
   + baseline trên gold. Lần này con số sẽ KHÔNG còn 1.0 ảo — điểm số trung thực đầu tiên cho báo cáo.

**Quyết định cần chốt:** nhãn `uncertain` / `exclude` → loại hẳn khỏi train (khuyến nghị).

---

## Phase 2 — Tạo `final_dataset.csv` (bước 9, đang thiếu)

Artifact khóa mở toàn bộ phần train so sánh. Thành phần đề xuất, theo thứ tự ưu tiên độ tin cậy:

| Nguồn | Nhãn | Vai trò |
|---|---|---|
| Human-reviewed (đợt 5 + 8) | gold | **trọng số cao nhất**, ưu tiên tuyệt đối |
| YouTube high-confidence weak | pseudo | nền dữ liệu lớn |
| PhoBERT confident (113K, prob≥0.9) | pseudo | *tùy chọn* — mở rộng nhưng có nhiễu |
| `data_unified/augmentation_negatives.csv` (42.952 external) | 0 | hard-negative chống "mọi câu buồn = trầm cảm" |

Sau đó: dedup theo text → cân bằng lớp → **split train/val/test in-domain**.
**Giữ `data_unified/cross_domain_test.csv` tách hẳn** — không bao giờ trộn vào train.

**3 quyết định cần chốt:**
- Có nhồi PhoBERT confident 113K vào không? (nhiều dữ liệu ↔ nhiều nhiễu)
- Có chạy **PhoBERT vòng 2** (train lại có thêm nhãn active-learning) trước khi chốt final không?
  Đây đúng tinh thần active-learning loop của pipeline.
- Tỷ lệ human:pseudo và cách cân bằng lớp.

---

## Phase 3 — Train dãy model so sánh (bước 10-13)

Tất cả train trên `final_dataset`, test trên **2 tập**: in-domain + cross-domain VSMEC cố định.

1. **TF-IDF + SVM** — hiện mới có TF-IDF + **LogReg**, *chưa phải SVM*. Thêm `LinearSVC`
   (tái dùng phần vectorizer word+char đã có trong `baseline_model.py`).
2. **BiLSTM** — **chưa tồn tại**, phải build mới (embedding tiếng Việt + BiLSTM + classifier).
   Phần code nặng nhất.
3. **PhoBERT (final)** — train lại trên `final_dataset` thật, không phải weak-label như "lần 1".
4. **PhoBERT + BERTopic** — chạy BERTopic trên `corpus_text_all.csv` (316K, đã có) để lấy topic,
   kết hợp đặc trưng chủ đề với PhoBERT.

---

## Phase 4 — So sánh & báo cáo (bước 14-15)

1. **Bảng tổng hợp** 5 model (baseline + 4) × 2 test set (in-domain / cross-domain):
   F1, precision, recall, confusion matrix. Bảng trung tâm của bài báo.
2. **Phân tích lỗi** — false positive/negative điển hình; tận dụng phát hiện đã có
   (baseline mù distress ngắn, recall keyword 0.91%).
3. Viết báo cáo dựa trên các report JSON tích lũy qua từng phase.

---

## Quyết định mở (sẽ hỏi lại khi file review về)

- **PhoBERT vòng 2?** có / không
- **Hồi 113K pseudo-label vào final?** có / không
- **Tỷ lệ human:pseudo** và cách cân bằng lớp
- **uncertain/exclude** loại khỏi train? (mặc định: có)

Khi nhận 2 file export, bắt đầu thẳng từ **Phase 1**.
