# 🧠 Mental Health AI Platform

Vietnamese Depression Detection via PhoBERT + BERTopic

A web demo platform for detecting depression indicators in Vietnamese text using state-of-the-art NLP models.

## 🚀 Quick Deploy

### Backend → Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

### Frontend → Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com)

See [DEPLOY_VERCEL_RAILWAY.md](../DEPLOY_VERCEL_RAILWAY.md) for detailed deployment guide.

## 🛠️ Local Development

```bash
# Frontend
cd web_demo
npm install
npm run dev

# Backend (separate terminal)
cd web_demo/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
JWT_SECRET_KEY="dev-secret-key" uvicorn main:app --reload
```

## 📁 Project Structure

```
web_demo/
├── src/                    # React frontend
│   ├── components/         # UI components
│   ├── pages/             # Page components
│   ├── services/          # API client
│   └── contexts/          # React contexts
├── backend/               # FastAPI backend
│   ├── inference/         # ML inference engines
│   ├── models/            # Trained models
│   ├── data/              # SQLite database
│   └── main.py            # API endpoints
└── tests/                 # Test suites
```

## 🔑 Default Credentials

| Username | Password |
|----------|----------|
| admin | admin123 |

## 📋 Features

- [x] Single text prediction
- [x] Batch CSV upload
- [x] YouTube video analysis
- [x] Prediction history
- [x] User authentication
- [x] Admin dashboard

## 🧪 Testing

```bash
cd web_demo
JWT_SECRET_KEY="dev-secret-key" pytest tests/ -v
```

## 📚 Documentation

- [Deployment Guide](../DEPLOY_VERCEL_RAILWAY.md)
- [API Documentation](http://localhost:8001/docs)
- [Model Training](../docs/)

## 📄 License

MIT
