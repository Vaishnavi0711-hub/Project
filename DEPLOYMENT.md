# TRUST.AI Deployment Guide

This guide covers deploying TRUST.AI to production with both frontend and backend components.

## Architecture Overview

```
┌─────────────────────────────────┐
│  Frontend (Next.js on Vercel)   │
│  - Landing page                 │
│  - Dashboard                     │
│  - API routes (proxy to backend) │
└──────────────┬──────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────┐
│  Backend (FastAPI + Python)     │
│  - Text analysis                │
│  - Audio analysis               │
│  - Model inference              │
└─────────────────────────────────┘
```

## Prerequisites

- GitHub account (for code hosting)
- Vercel account (for frontend)
- Backend hosting (Railway, Fly.io, Render, etc.)
- Python 3.10+ (for backend)
- Node.js 18+ (for frontend)

## Step 1: Prepare Code for Git

```bash
# Initialize git repository (if not already done)
git init

# Create .gitignore
echo "node_modules/" >> .gitignore
echo ".env.local" >> .gitignore
echo "backend/venv/" >> .gitignore
echo "__pycache__/" >> .gitignore

# Commit initial code
git add .
git commit -m "Initial TRUST.AI commit"
```

## Step 2: Deploy Frontend to Vercel

### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

### Option B: Connect GitHub Repository

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import project from GitHub
4. Configure:
   - Framework Preset: Next.js
   - Root Directory: ./
   - Build Command: `pnpm build`
   - Output Directory: `.next`

### Set Environment Variables in Vercel

1. Go to Project Settings → Environment Variables
2. Add: `BACKEND_URL` = `https://your-backend-url.com`
3. Redeploy

## Step 3: Deploy Backend

Choose one of the following options:

### Option A: Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create new project
railway init

# Deploy
railway up
```

Configure environment in Railway dashboard.

### Option B: Fly.io

```bash
# Install Fly CLI
curl https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly launch --generator-only

# Deploy
fly deploy
```

Create `fly.toml` in backend directory:

```toml
app = "trust-ai"
primary_region = "sjc"

[build]
  builder = "paketobuildpacks"

[env]
  PYTHONUNBUFFERED = "true"

[[services]]
  internal_port = 8000
  processes = ["app"]

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### Option C: Render

1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. New → Web Service
4. Connect GitHub repository (select `backend` subdirectory)
5. Configure:
   - Environment: Python 3.11
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
6. Add environment variables if needed
7. Deploy

### Option D: Self-Hosted (AWS EC2, DigitalOcean, etc.)

```bash
# SSH into server
ssh ubuntu@your-server-ip

# Install Python and dependencies
sudo apt update
sudo apt install python3.10 python3-pip

# Clone repository
git clone https://github.com/yourusername/trust-ai.git
cd trust-ai/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Use systemd for auto-restart
sudo nano /etc/systemd/system/trust-ai.service
```

Example systemd service file:

```ini
[Unit]
Description=TRUST.AI Backend
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/trust-ai/backend
Environment="PATH=/home/ubuntu/trust-ai/backend/venv/bin"
ExecStart=/home/ubuntu/trust-ai/backend/venv/bin/gunicorn \
    app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

## Step 4: Configure CORS

Update `backend/app/main.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.vercel.app",
        "https://your-custom-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 5: Set Up Custom Domain (Optional)

### Frontend (Vercel)
1. Go to Project Settings → Domains
2. Add custom domain
3. Update DNS records per Vercel instructions

### Backend
Configure DNS records pointing to your backend provider's servers.

## Step 6: Enable HTTPS

- Vercel: Automatic (Let's Encrypt)
- Railway: Automatic (automatic SSL)
- Fly.io: Automatic (Caddy reverse proxy)
- Render: Automatic (Let's Encrypt)
- Self-hosted: Use Let's Encrypt with Certbot

## Step 7: Monitor and Logs

### Vercel
- Go to Deployments → Select deployment → Function logs

### Railway
- Dashboard → Logs tab

### Fly.io
```bash
fly logs
```

### Render
- Dashboard → Logs

## Step 8: Performance Optimization

### Frontend
- Enable Image Optimization
- Configure ISR (Incremental Static Regeneration)
- Monitor Core Web Vitals

### Backend
- Add caching headers
- Implement rate limiting
- Monitor response times

```python
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

## Troubleshooting

### Backend connection fails
1. Check `BACKEND_URL` environment variable
2. Verify CORS configuration
3. Check backend logs for errors
4. Ensure backend is accessible from frontend origin

### Slow audio analysis
1. Upgrade backend CPU/memory
2. Implement caching for Whisper model
3. Use smaller Whisper model (tiny, base instead of large)
4. Add request queuing system

### High storage usage
1. Implement temporary file cleanup
2. Add data retention policies
3. Monitor disk usage

## Database (Future)

For production with user accounts:

```python
# Add to requirements.txt
databases==0.7.0
sqlalchemy==2.0.0
alembic==1.12.0
```

Create `backend/app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

## API Versioning

Update routes for API versioning:

```python
app.include_router(analyze_text.router, prefix="/api/v1", tags=["text"])
app.include_router(analyze_audio.router, prefix="/api/v1", tags=["audio"])
```

## Monitoring & Analytics

### Frontend Metrics
- Use Vercel Analytics
- Monitor Core Web Vitals
- Track user engagement

### Backend Metrics
- Response times
- Error rates
- Resource usage

### Error Tracking
- Integrate Sentry
- Set up CloudWatch alarms
- Monitor API latency

```bash
# Add Sentry
pip install sentry-sdk

# In app/main.py
import sentry_sdk
sentry_sdk.init("https://your-sentry-dsn@sentry.io/project-id")
```

## Scaling Considerations

### Horizontal Scaling
- Deploy multiple backend instances
- Use load balancer (nginx, HAProxy)
- Add caching layer (Redis)

### Vertical Scaling
- Increase server resources
- Upgrade to faster CPU
- Add more memory

## Cost Estimation (Monthly)

- **Vercel Frontend**: $0-20 (free tier available)
- **Railway/Render Backend**: $5-50 (depending on traffic)
- **Custom Domain**: $10-15/year
- **SSL Certificate**: Free (Let's Encrypt)

## Maintenance

- Update dependencies regularly: `pip install -U -r requirements.txt`
- Monitor security advisories
- Test deployments in staging first
- Keep backup of production data
- Review logs weekly

## Rollback Procedure

### Vercel
1. Go to Deployments
2. Click "Redeploy" on previous version

### Railway/Render/Fly
1. Revert code commit: `git revert <commit>`
2. Redeploy

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions)
2. Add automated testing
3. Implement user authentication
4. Add analytics dashboard
5. Scale to support more concurrent users

---

**Need help?** Check backend/app/main.py for detailed configuration options.
