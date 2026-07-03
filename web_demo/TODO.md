# Mental Health AI Platform - Development Roadmap

## Project Overview
Web demo cho hệ thống **PhoBERT + BERTopic Depression Detection** trên dữ liệu Vietnamese YouTube comments.

---

## ✅ Features Implemented (Hoàn thành)

### Frontend (React + TypeScript + TailwindCSS)
- [x] **Dashboard** - Hiển thị metrics tổng quan (sử dụng mock data)
- [x] **Single Prediction** - Phân tích 1 đoạn text (mock logic, chưa gọi API thật)
- [x] **Batch Prediction** - Upload CSV để phân tích nhiều comments (mock data)
- [x] **Topic Analysis** - Hiển thị 6 topics từ BERTopic (static data)
- [x] **Statistics** - Charts với Recharts (pie, bar, word cloud, confusion matrix)
- [x] **History** - Lịch sử predictions (local state, chưa persist)
- [x] **Model Comparison** - So sánh 4 models (TF-IDF+SVM, BiLSTM, PhoBERT, PhoBERT+BERTopic)
- [x] **UI Components** - Layout, Header, Cards, Buttons với Tailwind
- [x] **Routing** - React Router với 7 routes

### Backend (FastAPI)
- [x] **API Endpoints** - 6 endpoints được định nghĩa (mock data)
- [x] **CORS Middleware** - Cho phép cross-origin requests
- [x] **Pydantic Models** - Request/Response schemas
- [x] **Health Check** - `/api/health` endpoint

### Dev Environment
- [x] **Frontend Dev Server** - Vite chạy trên port 3000
- [x] **Backend Dev Server** - Uvicorn chạy trên port 8001
- [x] **Docker Setup** - Dockerfile và docker-compose.yml

---

## 🔄 In Progress / Partially Implemented (Đang làm dở)

### Backend
- [ ] **Model Loading** - Chưa load thực sự PhoBERT model
- [ ] **Real Prediction** - API `/api/predict` trả về mock data, chưa inference thật
- [ ] **BERTopic Integration** - Chưa khởi tạo BERTopic service

### Frontend
- [ ] **API Integration** - Phần lớn pages sử dụng mock data thay vì gọi API
- [ ] **Vite Proxy Config** - Đang trỏ đến port 8000, cần cập nhật sang 8001

---

## ❌ Not Implemented / TODO (Cần làm thêm)

### Critical (Cần thiết cho đề tài)

#### 1. Real Model Integration
- [ ] Load PhoBERT model từ `models/bilstm/phobert/`
- [ ] Implement inference pipeline cho depression detection
- [ ] Integrate data augmentation models (nếu cần)
- [ ] Handle GPU/CPU device selection

#### 2. BERTopic Integration
- [ ] Load BERTopic model đã train
- [ ] Topic inference cho new texts
- [ ] Dynamic topic visualization

#### 3. Real Data Integration
- [ ] Connect với YouTube crawler data (comments đã crawl)
- [ ] Database schema cho predictions history (SQLite/PostgreSQL)
- [ ] Batch processing với dữ liệu thật từ YouTube

#### 4. API Backend Enhancement
- [ ] Fix proxy config (port 8001 thay vì 8000)
- [ ] Real-time prediction endpoint
- [ ] Batch prediction với file upload thật
- [ ] Export results sang CSV/Excel

### Important (Nâng cao trải nghiệm)

#### 5. YouTube Integration
- [ ] Paste YouTube video URL để fetch comments
- [ ] Analyze all comments từ 1 video
- [ ] Display video metadata (title, channel, view count)

#### 6. Enhanced Statistics
- [ ] Real-time metrics từ model evaluation
- [ ] Interactive charts (filter by date range, topic)
- [ ] Export statistics report

#### 7. User Features
- [ ] Save predictions to database
- [ ] User authentication (optional)
- [ ] Share prediction results

#### 8. Deployment
- [ ] Environment variables configuration
- [ ] Production build optimization
- [ ] Docker deployment với GPU support
- [ ] CI/CD pipeline

---

## 📊 Project Alignment Checklist

Để web demo bám sát đề tài nghiên cứu:

### Research Components → Demo Features
| Research Component | Demo Feature | Status |
|-------------------|--------------|--------|
| PhoBERT + BERTopic Model | Model Comparison | ✅ Done |
| Vietnamese YouTube Comments | Batch Prediction + YouTube Integration | ❌ Need real data |
| Active Learning (Round 4) | Model training status | ❌ Not shown |
| Data Augmentation | Augmented data indicator | ❌ Not shown |
| Cross-domain Evaluation | Domain adaptation stats | ❌ Not shown |
| BERTopic Topics | Topic Analysis Page | ✅ Done |
| Depression Detection | Prediction Page | 🔄 Mock only |

### Missing Research Elements to Demo
- [ ] Show active learning rounds progress
- [ ] Display data augmentation statistics
- [ ] Cross-domain performance metrics
- [ ] Model training history
- [ ] Sample efficiency (labeled vs unlabeled data)

---

## 🛠 Technical Debt

1. **Port mismatch**: Vite proxy → 8000, Backend → 8001
2. **Mock data leakage**: Nhiều components dùng mock thay vì API
3. **No persistence**: History không được lưu vào database
4. **No error handling**: Chưa có loading states, error boundaries
5. **No caching**: API responses không được cache

---

## 🚀 Priority Tasks

### Week 1: Core Functionality
1. [ ] Fix Vite proxy config (port 8001)
2. [ ] Connect frontend to real backend API
3. [ ] Load và serve PhoBERT model
4. [ ] Implement real single prediction endpoint

### Week 2: Data Pipeline
5. [ ] Integrate YouTube data source
6. [ ] Implement batch prediction với real data
7. [ ] Add SQLite database cho history
8. [ ] Implement BERTopic topic inference

### Week 3: Research Integration
9. [ ] Add active learning round indicator
10. [ ] Display data augmentation stats
11. [ ] Show cross-domain evaluation results
12. [ ] Add model training timeline

### Week 4: Polish
13. [ ] Error handling và loading states
14. [ ] Performance optimization
15. [ ] Documentation
16. [ ] Deployment setup

---

## 📁 Key Files Reference

```
web_demo/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx      # Metrics overview
│   │   │   ├── Prediction.tsx     # Single text analysis (MOCK)
│   │   │   ├── BatchPrediction.tsx # CSV upload (MOCK)
│   │   │   ├── Topics.tsx         # BERTopic topics
│   │   │   ├── Statistics.tsx     # Charts
│   │   │   ├── History.tsx        # Prediction history
│   │   │   └── ModelComparison.tsx # Model comparison
│   │   ├── services/api.ts        # API client (not fully used)
│   │   └── data/mockData.ts       # Mock data (needs real integration)
│   └── vite.config.ts             # Proxy config (needs fix)
├── backend/
│   ├── main.py                    # FastAPI app (MOCK endpoints)
│   └── requirements.txt
└── TODO.md                        # This file
```

---

## 🔗 External Resources

- PhoBERT Model: `models/bilstm/phobert/model.pt`
- Random Init Model: `models/bilstm/random/model.pt`
- Active Learning Data: `docs/label_studio_round4_active_learning_*.csv`
- Research Paper: Báo cáo trong repo

---

*Last Updated: 2026-07-03*
