# 🚀 Deploy Mental Health AI Platform lên Vercel + Railway

Hướng dẫn chi tiết để deploy web demo lên **Vercel** (frontend) và **Railway** (backend).

---

## 📋 Prerequisites

- [ ] GitHub account
- [ ] Vercel account (đăng nhập bằng GitHub)
- [ ] Railway account (đăng nhập bằng GitHub)
- [ ] Git initialized local project
- [ ] Google Cloud YouTube API key (đã có)

---

## 🏗️ Kiến trúc Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                        Vercel                                │
│                    (Frontend - React)                        │
│                   https://your-app.vercel.app               │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Railway                                │
│                  (Backend - FastAPI)                        │
│               https://your-backend.railway.app              │
│                    (with GPU support)                        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐    ┌──────────┐    ┌──────────┐
        │ PhoBERT │    │ SQLite   │    │  YouTube │
        │ Model   │    │ Database │    │   API    │
        └─────────┘    └──────────┘    └──────────┘
```

---

## 📁 Chuẩn bị Repository

### 1. Fork/Copy project lên GitHub

```bash
# Nếu chưa có git remote
cd /Users/iannwendy/Documents/crawl_yt/youtube_depression_crawler
git init
git add .
git commit -m "Initial commit"

# Tạo repo mới trên GitHub, sau đó:
git remote add origin https://github.com/YOUR_USERNAME/your-repo-name.git
git push -u origin main
```

### 2. Tách Frontend và Backend

**Phương án A: Monorepo (đơn giản hơn)**

Giữ nguyên cấu trúc hiện tại, deploy riêng:

```
web_demo/
├── src/                 # Frontend (Vercel)
├── backend/             # Backend (Railway)
└── web_demo/            # Root config
```

**Phương án B: Tách hoàn toàn** (tạo 2 repos)

Tạo 2 repos riêng cho frontend và backend.

---

## 🎨 DEPLOY BACKEND LÊN RAILWAY

### Bước 1: Tạo Railway Project

1. Truy cập https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Chọn repository chứa backend
4. Chọn branch: `main`

### Bước 2: Cấu hình Build Command

Railway sẽ tự động detect Django/FastAPI. Cấu hình thủ công:

1. Trong project settings:
   - **Root Directory**: `web_demo/backend` (hoặc `.` nếu backend là root)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Bước 3: Cấu hình Environment Variables

Trong Railway dashboard → **Variables**:

```env
# Required
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
YOUTUBE_API_KEY=AIzaSyBgf4UYp_0OIelNXGgdPc96rYoGTRYR36c

# Optional (tùy cấu hình)
PHOBERT_DEVICE=cpu
HF_HUB_OFFLINE=0
PYTHONUNBUFFERED=1
```

### Bước 4: Cấu hình Database

**SQLite** (miễn phí, đủ cho demo):
- Không cần setup gì thêm
- Railway sẽ persist data trong `/data`

**PostgreSQL** (production khuyến nghị):

1. Trong Railway project → **New** → **Database** → **PostgreSQL**
2. Sau khi tạo, copy connection string
3. Thêm vào Environment Variables:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Bước 5: Mount Models Directory

Để load PhoBERT model, cần mount volume:

1. Trong Railway project → **Settings** → **Volumes**
2. Create volume: `models-volume`
3. Mount vào path: `/app/models`

Upload models folder lên Railway:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
cd /Users/iannwendy/Documents/crawl_yt/youtube_depression_crawler/web_demo/backend
railway link

# Upload models (chọn folder models/)
railway run mkdir -p /app/models
railway upload ./models /app/models
```

### Bước 6: Kiểm tra Deployment

1. Đợi Railway build xong (~3-5 phút)
2. Click vào deployment mới nhất
3. Copy URL: `https://your-backend.railway.app`

Test API:
```bash
curl https://your-backend.railway.app/api/health
```

Expected response:
```json
{"status":"healthy","timestamp":"2026-09-05T..."}
```

---

## 🌐 DEPLOY FRONTEND LÊN VERCEL

### Bước 1: Cấu hình Frontend

Update `web_demo/src/services/api.ts` để dùng backend URL từ environment:

```typescript
// web_demo/src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Railway URL format: https://backend.railway.app
// Production: https://your-app.railway.app
```

### Bước 2: Tạo Environment File

Tạo file `web_demo/.env.production`:

```env
VITE_API_URL=https://your-backend.railway.app
VITE_APP_NAME=Mental Health AI
```

### Bước 3: Deploy lên Vercel

**Cách 1: Qua Dashboard**

1. Truy cập https://vercel.com
2. Click **"Add New..."** → **"Project"**
3. Import GitHub repository
4. Set **Root Directory**: `web_demo`
5. **Framework Preset**: Vite
6. **Build Command**: `npm run build`
7. **Output Directory**: `dist`
8. **Environment Variables**:
   - `VITE_API_URL` = `https://your-backend.railway.app`
9. Click **Deploy**

**Cách 2: Qua Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
cd /Users/iannwendy/Documents/crawl_yt/youtube_depression_crawler/web_demo
vercel login

# Deploy (interactive)
vercel

# Deploy to production
vercel --prod
```

### Bước 4: Cấu hình Rewrites (Proxy)

Tạo file `web_demo/vercel.json`:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.railway.app/api/:path*"
    }
  ]
}
```

Hoặc cấu hình trong Vercel Dashboard:
- **Project Settings** → **Environment Variables**
- **Project Settings** → **Regions** → Chọn region gần backend

### Bước 5: Custom Domain (Optional)

1. Trong Vercel Dashboard → **Domains**
2. Thêm domain của bạn
3. Cập nhật DNS records theo hướng dẫn

---

## 🔒 CẤU HÌNH BẢO MẬT

### 1. CORS Configuration

Update backend `main.py` để cho phép Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",
        "http://localhost:3000",  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. JWT Secret

**IMPORTANT**: Đổi JWT_SECRET_KEY trong Railway:

```bash
# Generate new secret
openssl rand -base64 32
```

### 3. Environment Variables

Đảm bảo **"Encrypt"** được bật cho các biến nhạy cảm trong Railway.

---

## ✅ CHECKLIST TRƯỚC KHI DEPLOY

```markdown
Backend (Railway):
- [ ] JWT_SECRET_KEY đã đổi
- [ ] YOUTUBE_API_KEY đã set
- [ ] Models đã upload
- [ ] Database đã init
- [ ] Health check hoạt động

Frontend (Vercel):
- [ ] VITE_API_URL đã set đúng
- [ ] Build thành công
- [ ] Rewrites/proxy đã cấu hình
- [ ] CORS backend đã allow Vercel domain
```

---

## 🧪 TEST SAU DEPLOY

### Test Backend
```bash
curl https://your-backend.railway.app/api/health
curl https://your-backend.railway.app/api/youtube/validate?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Test Frontend
1. Truy cập https://your-app.vercel.app
2. Đăng nhập (admin/admin123)
3. Test single prediction
4. Test batch upload
5. Test YouTube analysis

### Test Authentication
```bash
curl -X POST https://your-backend.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## 🔧 TROUBLESHOOTING

### Lỗi 1: CORS Error

```
Access to fetch at 'https://backend.railway.app' from origin 'https://app.vercel.app' 
has been blocked by CORS policy
```

**Fix**: Update CORS origins trong backend `main.py`

---

### Lỗi 2: 502 Bad Gateway

Backend không start được.

**Fix**:
1. Check Railway logs
2. Verify start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Verify `$PORT` env variable được set

---

### Lỗi 3: Model not found

```
FileNotFoundError: [Errno 2] No such file or directory: '/app/models/...'
```

**Fix**:
1. Verify models folder được mount đúng
2. Check models path trong code
3. Re-upload models nếu cần

---

### Lỗi 4: PhoBERT device error

**Fix**: Set `PHOBERT_DEVICE=cpu` trong Railway environment variables

---

### Lỗi 5: YouTube API quota exceeded

```
"quotaExceeded"
```

**Fix**: Chờ đợi hoặc xin quota increase từ Google Cloud Console

---

## 💰 CHI PHÍ

### Railway
| Plan | Features | Price |
|------|----------|-------|
| **Hobby** | 500 hours/month, 1GB RAM | **Free** |
| Starter | 1000 hours, 2GB RAM, 1GB disk | $5/month |
| Pro | Unlimited, 4GB RAM, GPU support | $20/month |

**Note**: PhoBERT cần CPU, có thể dùng Hobby plan.

### Vercel
| Plan | Features | Price |
|------|----------|-------|
| **Hobby** | 100GB bandwidth, SSR | **Free** |
| Pro | Unlimited, Analytics | $20/month |

---

## 📞 SUPPORT

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Railway Discord**: https://discord.gg/railway
- **Vercel Discord**: https://discord.gg/vvercel

---

## 🎉 DEPLOYMENT COMPLETE

Sau khi deploy thành công:

1. **Frontend**: `https://your-app.vercel.app`
2. **Backend API**: `https://your-backend.railway.app`
3. **API Docs**: `https://your-backend.railway.app/docs`

**Login credentials** (default):
- Username: `admin`
- Password: `admin123`

**Đổi password sau khi deploy**:
```bash
curl -X POST https://your-backend.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"NEW_SECURE_PASSWORD"}'
```

---

## 🔄 CI/CD Setup (Optional)

### GitHub Actions cho Railway

Tạo file `.github/workflows/railway.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]
    paths: ['web_demo/backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        uses: vectordotdev/railway-github-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend
```

### GitHub Actions cho Vercel

1. Cài đặt Vercel GitHub App
2. Vercel sẽ auto-deploy khi có push

---

## 📊 MONITORING

### Railway Metrics
- Memory, CPU usage
- Request logs
- Error tracking

### Vercel Analytics
- Page views
- Performance
- Core Web Vitals

---

**Chúc bạn deploy thành công! 🚀**
