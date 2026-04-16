# ASGI Application Guide

## What is ASGI?

**ASGI** = Asynchronous Server Gateway Interface

### Simple Explanation
- **WSGI** (older): Server talks to Python web app synchronously (one request at a time)
- **ASGI** (modern): Server talks to Python web app asynchronously (multiple requests simultaneously)

FastAPI uses ASGI because it's designed for async/await operations.

### The Command Format
```bash
uvicorn app.main:app --reload --port 8000
```

Breaking it down:
- `uvicorn` = ASGI server (runs the app)
- `app.main` = Module path (folder/file, not .py extension)
  - `app` = folder name (c:\Users\LPAdmin\Trust.ai\backend\app\)
  - `main` = file name (main.py)
- `:app` = Variable name in that file
  - In main.py: `app = FastAPI(...)`
- `--reload` = Restart server on code changes
- `--port 8000` = Which port to listen on

## Common ASGI Errors & Solutions

### Error 1: "No module named 'app'"
**Cause:** Wrong working directory
**Solution:** Run from project root
```bash
cd c:\Users\LPAdmin\Trust.ai
python -m uvicorn app.main:app --reload --port 8000
# ❌ WRONG (you're in backend folder)
cd c:\Users\LPAdmin\Trust.ai\backend
python -m uvicorn app.main:app --reload --port 8000
```

### Error 2: "Cannot find attribute 'app'"
**Cause:** Variable name doesn't match
**Solution:** Check main.py has `app = FastAPI(...)`
```python
# main.py - must have this line
app = FastAPI(title="TRUST.AI API", ...)

# Then command should be:
uvicorn app.main:app
#                    ^^^ Variable name
```

### Error 3: "No module named 'uvicorn'"
**Cause:** Uvicorn not installed
**Solution:** Install in virtual environment
```bash
# Activate virtual environment first
C:\Users\LPAdmin\Trust.ai\.venv\Scripts\activate

# Then install
pip install uvicorn
```

## Proper Way to Run the Backend

### Method 1: Using Virtual Environment (RECOMMENDED)
```bash
# Navigate to project root
cd C:\Users\LPAdmin\Trust.ai

# Activate virtual environment
.\.venv\Scripts\activate

# Run uvicorn
python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
```

### Method 2: Direct Python from venv
```bash
cd C:\Users\LPAdmin\Trust.ai
"C:\Users\LPAdmin\Trust.ai\.venv\Scripts\python" -m uvicorn app.main:app --reload --port 8000
```

### Method 3: From Backend Directory
```bash
cd C:\Users\LPAdmin\Trust.ai\backend
..\..\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

## What the Backend Does

Once running on http://127.0.0.1:8000:

```
GET  /health                    → Check if online
POST /api/analyze-text          → Analyze text for scams
POST /api/analyze-audio         → Analyze audio (speech-to-text + deepfake detection)
POST /api/feedback/audio        → Submit feedback (improves model)
GET  /api/feedback/status       → Check online learning status
POST /api/feedback/flush        → Force model training
GET  /api/health/learning       → Check learning service status
```

## Verify It's Working

### Check Health Endpoint
```bash
# In another terminal
curl http://127.0.0.1:8000/health

# Expected response:
{"status":"ok","service":"trust-ai-backend"}
```

### Check API Documentation (Interactive)
Visit in browser:
- http://127.0.0.1:8000/docs (Swagger UI - try API calls here!)
- http://127.0.0.1:8000/redoc (ReDoc - API documentation)

## Expected Startup Output

When backend starts correctly, you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
============================================================
BACKEND STARTUP
============================================================
✓ CNN/torch dependencies available
Loading trained CNN model from: C:\Users\LPAdmin\Trust.ai\backend\models\cnn_deepfake_best.pt
Model file exists: True
✓ CNN model architecture created
✓ Online learning service initialized
============================================================
INFO:     Application startup complete
```

If you see all those checkmarks (✓), the improved CNN model is loaded and working!

## Next: Test the Model

Once backend is running, test it with:

```bash
# In a new terminal
cd C:\Users\LPAdmin\Trust.ai
python backend/training/test_improvements.py
```

This will:
1. Test prediction consistency (same audio = same score)
2. Test scam detection sensitivity
3. Test genuine audio handling
4. Show ensemble voting in action
