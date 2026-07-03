# Mental Health AI Platform

Depression Detection System using PhoBERT + BERTopic for Vietnamese Social Media Texts

## Quick Start (Single Command)

```bash
cd web_demo
make dev
```

Hoặc với Docker:

```bash
cd web_demo
make up
```

**Truy cập:** http://localhost:3000

---

## Available Commands

| Command | Description |
|---------|-------------|
| `make dev` | Run in development mode (npm + python) |
| `make up` | Run with Docker |
| `make down` | Stop Docker containers |
| `make build` | Build Docker images only |
| `make logs` | View Docker logs |
| `make clean` | Stop and remove containers |

---

## Development Without Makefile

### Frontend

```bash
cd web_demo
npm install
npm run dev
# → http://localhost:3000
```

### Backend

```bash
cd web_demo/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs
```

---

## Project Structure

```
web_demo/
├── Makefile                 # Single command deployment
├── docker-compose.yml       # Docker configuration
├── Dockerfile              # Frontend build
├── frontend/               # React + TypeScript + TailwindCSS
│   ├── src/
│   │   ├── components/    # UI Components
│   │   ├── pages/         # Page Components
│   │   ├── data/          # Mock Data
│   │   └── types/         # TypeScript Types
│   └── Dockerfile
├── backend/                # FastAPI Backend
│   ├── main.py            # API Endpoints
│   ├── requirements.txt
│   └── Dockerfile
├── nginx.conf             # Reverse proxy config
└── README.md
```

## Features

1. **Dashboard** - System overview with metrics
2. **Text Prediction** - Single text analysis
3. **Batch Prediction** - CSV file upload
4. **Topic Analysis** - BERTopic visualization
5. **Statistics** - Charts and metrics
6. **History** - Prediction history
7. **Model Comparison** - Model performance

## Tech Stack

- **Frontend**: React 18, TypeScript, TailwindCSS, Recharts
- **Backend**: FastAPI, Pydantic
- **AI Models**: PhoBERT, BERTopic
- **Proxy**: Nginx
- **Container**: Docker

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Dashboard statistics |
| POST | `/api/predict` | Single text prediction |
| POST | `/api/predict/batch` | Batch prediction |
| GET | `/api/topics` | Topic analysis |
| GET | `/api/models/comparison` | Model comparison |

## Stop Services

```bash
make down        # Docker
# or
pkill -f uvicorn && pkill -f vite   # Dev mode
```
