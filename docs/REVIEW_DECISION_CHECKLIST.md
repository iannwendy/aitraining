# Checklist chốt ngay khi file review 1.500 dòng về

Đây là bản "ready to execute" của phần cuối [ROADMAP_SAU_REVIEW.md](ROADMAP_SAU_REVIEW.md).
Đọc khi 2 file export Label Studio (`label_studio_step5_review_export.csv` +
`label_studio_step8_active_learning_export.csv`) đã có trong `docs/`.

Mỗi mục có **gợi ý mặc định** dựa trên evidence đã có trong repo (xem ghi chú).
User confirm/override trước khi chạy.

---

## Phase 1 — Ghép nhãn & khôi định gold

- [ ] **Merge** `label_studio_step5_review_export.csv` ↔ `docs/label_studio_step5_review_key.csv` qua `row_id`
- [ ] **Merge** `label_studio_step8_active_learning_export.csv` ↔ `docs/label_studio_step8_active_learning_key.csv` qua `row_id`
- [ ] **Đo tỷ lệ bất đồng người-máy** (sau khi normalize vocab: `depression_auto` → `depression`)
  - Script tham khảo: `/tmp/check_gold_quality2.py` (đã có trong repo history).
  - **PASS ngưỡng:** depression_auto bị reject (flipped sang normal) ≥ 30%.
  - Evidence hiện tại: 92/150 = **61% giữ depression**, **39% flipped → normal** — đạt chuẩn.
- [ ] **Tỷ lệ uncertain + exclude** ghi nhận; mặc định **LOẠI khỏi train** (xem Quyết định 4).
- [ ] **Rebuild gold** → ghi đè `data/gold_review.csv` với cả hai nguồn merged.
- [ ] **Chạy lại baseline trên gold mới**, kiểm tra accuracy **không** trở lại 1.0.
  - Evidence hiện tại: baseline F1=0.597, accuracy=0.71. Mức hợp lý.

---

## Phase 2 — Build `final_dataset.csv`

- [ ] **Quyết định 1 — PhoBERT vòng 2?** (retrain với thêm nhãn active-learning)
  - **Mặc định: KHÔNG.** Lý do: gold cũ + active learning samples đã được PhoBERT lần 1 dùng để
    chọn mẫu uncertainty. Retrain thêm một vòng chỉ tốn ~95 phút/CPU và rủi ro overfit vào
    active-learning bias.
  - **Chọn CÓ** nếu: muốn đạt ceiling F1, chấp nhận thêm ~6 giờ compute, có validation set
    đủ mạnh để early-stop.
- [ ] **Quyết định 2 — Hồi 113K pseudo-label (PhoBERT confident) vào final?**
  - **Mặc định: KHÔNG.** Lý do: 113K pseudo đa phần là `confidence=high` đã được weak-labeler
    gán (round 1 chỉ chọn uncertain/low confidence). Hồi vào = inflate class imbalance theo
    hướng keyword (đã có evidence keyword recall 0.91% trên distress ngắn).
  - **Chọn CÓ** nếu: muốn ablation so sánh, có thời gian, accept thêm noise.
- [ ] **Quyết định 3 — Tỷ lệ human:pseudo**
  - **Mặc định:** human (gold + active-learning có nhãn) làm trọng số cao (weight ≥ 1.0),
    pseudo chỉ dùng cho class `normal` ở weight 0.3-0.5 (anti-class-imbalance, không
    chi phối decision boundary).
  - File `final_train.csv` hiện tại đã có cột `weight` (xem header), dùng được luôn.
- [ ] **Quyết định 4 — `uncertain` / `exclude` loại khỏi train?**
  - **Mặc định: CÓ, LOẠI.** Lý do: giữ lại sẽ ép model học một class không tồn tại
    trong evaluation schema (label ∈ {0, 1}).
- [ ] **Dedup theo `comment_text`** (giữ entry có weight cao nhất khi trùng)
- [ ] **Cân bằng lớp** — kiểm tra distribution cuối; nếu `depression` < 30%, oversample
  hoặc class_weight trong loss.
- [ ] **Split 70/15/15** train/val/test in-domain, **giữ** `data_unified/cross_domain_test.csv` tách hẳn.
- [ ] **Ghi đè** `data/final_train.csv` + `data/final_val.csv` + `data/final_test.csv`.

---

## Phase 3 — Re-train so sánh

- [ ] TF-IDF + SVM (đã có baseline + LogReg; **cần thêm LinearSVC**)
- [ ] BiLSTM — **chưa có**, build mới
- [ ] PhoBERT (final) — train lại với `final_dataset` mới
- [ ] PhoBERT + BERTopic — chạy BERTopic trên `corpus_text_all.csv` nếu chưa

---

## Phase 4 — Báo cáo

- [ ] Bảng tổng hợp 5 model × 2 test set (in-domain / VSMEC)
- [ ] Error analysis trên `final_dataset` mới
- [ ] Update [docs/paper_report.html](paper_report.html) nếu headline numbers đổi

---

## Cross-domain test (VSMEC) — sanity check bắt buộc

Trước khi chạy Phase 3, verify test set chưa bị leak vào train:

```bash
.venv/bin/python -c "
import pandas as pd
train = pd.read_csv('data/final_train.csv')
vsmec = pd.read_csv('data_unified/cross_domain_test.csv')
overlap = set(train['comment_text']) & set(vsmec['comment_text'])
print(f'overlap: {len(overlap)} rows')
"
```

Kỳ vọng: 0 overlap. Nếu >0, dedup trước khi train.