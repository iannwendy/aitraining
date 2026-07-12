# Mental Health AI Platform - Development Roadmap

## Project Overview
Web demo cho hệ thống **PhoBERT + BERTopic Depression Detection** trên dữ liệu Vietnamese YouTube comments.

---

## ✅ Features Implemented (Hoàn thành)

### Frontend (React + TypeScript + TailwindCSS)
- [x] **Dashboard** - Hiển thị metrics tổng quan từ API thật
- [x] **Single Prediction** - Phân tích 1 đoạn text, gọi PhoBERT inference
- [x] **Batch Prediction** - Upload CSV để phân tích nhiều comments (gọi API)
- [x] **Topic Analysis** - Hiển thị topics từ BERTopic (API thật)
- [x] **Statistics** - Charts từ real data (confusion matrix, class distribution)
- [x] **History** - Lịch sử predictions từ SQLite database (persist)
- [x] **Model Comparison** - So sánh 9 models (TF-IDF, BiLSTM, PhoBERT, DAPT, aug)
- [x] **UI Components** - Layout, Header, Cards, Buttons với Tailwind
- [x] **Routing** - React Router với 7 routes
- [x] **i18n** - Hỗ trợ tiếng Việt/tiếng Anh

### Backend (FastAPI)
- [x] **PhoBERT Engine** - Load và inference round5 best_model thật
- [x] **BERTopic Engine** - Topic assignment từ trained model
- [x] **Metrics Loader** - Đọc metrics từ JSON files (baseline, bilstm, phobert, aug)
- [x] **DAPT Counter-Experiment** - Hiển thị DAPT results với badges
- [x] **Results Registry** - Auto-update mechanism cho training rounds
- [x] **SQLite Database** - Prediction history persistence
- [x] **Auto-save** - Mỗi prediction tự động lưu vào DB
- [x] **Hot-reload** - POST /api/models/refresh để reload không cần restart
- [x] **Health Check** - `/api/health` endpoint
- [x] **CORS Middleware** - Cho phép cross-origin requests

### Dev Environment
- [x] **Frontend Dev Server** - Vite chạy trên port 3000
- [x] **Backend Dev Server** - Uvicorn chạy trên port 8000 (đã fix)
- [x] **Docker Setup** - Multi-stage Dockerfile + docker-compose với volume mounts
- [x] **GPU Support** - Dockerfile hỗ trợ MPS (Apple Silicon) / CUDA

---

## 🔄 In Progress / Partially Implemented (Đang làm dở)

### Backend
- [ ] **BiLSTM Engine** - Chưa có vì heavy (vocab.json + model.pt inference phức tạp)
- [ ] **TF-IDF Engine** - Chưa cần thiết (PhoBERT đã tốt hơn)

### Frontend
- [ ] **Scatter Chart** - ModelComparison dùng ScatterChart nhưng chưa vẽ điểm đúng (Recharts Scatter dùng pixel coords chứ không phải data coords)

---

## ❌ Not Implemented / TODO (Cần làm thêm)

### Critical (Cần thiết cho đề tài)

#### 1. YouTube Integration
- [ ] Paste YouTube video URL để fetch comments
- [ ] Analyze all comments từ 1 video
- [ ] Display video metadata (title, channel, view count)

#### 2. Error Handling
- [ ] Loading states cho tất cả pages (đã có skeleton nhưng chưa hoàn chỉnh)
- [ ] Error boundaries / retry logic
- [ ] API timeout handling

#### 3. Deployment
- [ ] GPU support trong Docker (CUDA base image)
- [ ] CI/CD pipeline
- [ ] Production build optimization

### Important (Nâng cao trải nghiệm)

#### 4. Interactive Features
- [ ] Date range filter cho charts
- [ ] Topic filter cho batch prediction results
- [ ] Prediction sharing (copy link / share to social)

#### 5. User Features
- [ ] User authentication
- [ ] Multi-user prediction history
- [ ] Export statistics report as PDF

---

## 📊 Project Alignment Checklist

Để web demo bám sát đề tài nghiên cứu:

| Research Component | Demo Feature | Status |
|-------------------|-------------|--------|
| PhoBERT + BERTopic Model | Model Comparison | ✅ Done |
| Vietnamese YouTube Comments | Batch Prediction | ✅ Done |
| Active Learning (Round 5) | Results Registry + Refresh | ✅ Done |
| Data Augmentation | Model Comparison (+aug variants) | ✅ Done |
| Cross-domain Evaluation (VSMEC) | Cross-Domain F1 column | ✅ Done |
| DAPT Counter-Experiment | DAPT badge + note | ✅ Done |
| BERTopic Topics | Topic Analysis Page | ✅ Done |
| Depression Detection | Prediction Page | ✅ Done |
| History Persistence | SQLite DB | ✅ Done |

---

## 🛠 Technical Debt

1. ~~**Port mismatch**~~ ✅ Fixed: Vite proxy → 8000, Backend → 8000
2. ~~**Mock data leakage**~~ ✅ Fixed: Tất cả pages gọi API thật
3. ~~**No persistence**~~ ✅ Fixed: SQLite database cho history
4. ~~**No auto-update**~~ ✅ Fixed: Results Registry + hot-reload endpoint
5. **BiLSTM inference** - Chưa implement (heavy, cần vocab + model.pt loading)
6. **YouTube crawler integration** - Chưa có endpoint fetch comments từ URL

---

## 🚀 Next Steps (Sau khi Round 5 merge xong)

1. Chạy `scripts/merge_round5_active_learning.py` sau khi có labels từ Label Studio
2. Train lại models với dataset mới (6,079 → ~8,000+ rows)
3. Gọi `POST /api/models/refresh` — dashboard tự update mà không cần code change

---

## 📁 Key Files Reference

```
web_demo/
├── backend/
│   ├── main.py                    # FastAPI app với real inference
│   ├── database.py                # SQLite CRUD
│   ├── requirements.txt           # ML dependencies
│   ├── Dockerfile                # Multi-stage build
│   └── inference/
│       ├── phobert_engine.py     # PhoBERT classification
│       ├── bertopic_engine.py    # BERTopic topic assignment
│       ├── metrics_loader.py      # Parse metrics JSON files
│       └── registry.py           # Results registry reader/writer
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx         # Stats từ API
│   │   ├── Prediction.tsx        # Single prediction
│   │   ├── BatchPrediction.tsx  # CSV batch prediction
│   │   ├── Topics.tsx           # BERTopic topics
│   │   ├── Statistics.tsx        # Confusion matrix + distribution
│   │   ├── History.tsx          # SQLite-backed history
│   │   └── ModelComparison.tsx   # 9 models + DAPT + scatter
│   ├── services/api.ts           # API client
│   └── types/index.ts            # TypeScript interfaces
├── vite.config.ts                # Proxy → localhost:8000
└── docker-compose.yml            # Volume mounts: models/, data/, backend/
```

---

## 🔗 Model Paths (Docker)

```
/app/models/                       ← mounted from project/models/
  round5_predictions/best_model/   ← PhoBERT fine-tuned (latest)
  phobert_base_local/            ← PhoBERT tokenizer
  bertopic/bertopic_model.pkl    ← BERTopic trained model
  bilstm/                        ← BiLSTM checkpoints
  tfidf_*.joblib                ← TF-IDF baseline models

/app/data/                        ← mounted from project/data/
  gold_review.csv                ← 3,020 human-labeled
  final_dataset.csv              ← 6,079 total
  cleaned_comments.csv           ← 125,329 comments
  predictions.db                 ← SQLite history (created at runtime)
```

---

*Last Updated: 2026-07-11*
