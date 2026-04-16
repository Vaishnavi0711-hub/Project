# TRUST.AI Quick Start Guide

Get TRUST.AI running locally in 5 minutes.

## Prerequisites

- Node.js 18+ and pnpm
- Python 3.10+
- Git

## 1. Clone/Setup Repository

```bash
# If starting fresh
git clone <your-repo-url>
cd trust-ai

# Install frontend dependencies
pnpm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

## 2. Start the Backend

In one terminal:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Backend will be available at: **http://localhost:8000**

View API docs: **http://localhost:8000/docs**

## 3. Start the Frontend

In another terminal:

```bash
pnpm dev
```

Frontend will be available at: **http://localhost:3000**

## 4. Test the Application

1. Go to **http://localhost:3000**
2. Click "Analyze Now" button
3. Go to Dashboard
4. Try the example scam messages:
   - Click "Phishing example" button
   - Click "Analyze Message"
   - See the risk score and analysis

## Example Scam Messages to Test

### Text Analysis
- **Phishing**: "Click here immediately! Your PayPal account will be limited. Verify your account now: http://paypal-verify.com"
- **Prize Scam**: "You have won $1,000,000! Claim your prize now by sending $50 for processing fees."
- **Bank Fraud**: "Hi, your bank detected suspicious activity. Verify your credentials: bankverify.net"

### Audio Analysis
1. Go to "Audio Calls" tab
2. Click "Record Audio" and say something like:
   - "Hi, this is your bank. Please provide your social security number."
   - "Congratulations, you won a prize!"
3. Click "Analyze Audio"

## File Structure

```
trust-ai/
├── app/                      # Next.js app directory
│   ├── page.tsx             # Landing page
│   ├── dashboard/           # Dashboard pages
│   └── api/                 # API routes (proxy to backend)
├── components/              # React components
│   ├── MessageAnalyzer.tsx
│   ├── AudioAnalyzer.tsx
│   ├── ResultsPanel.tsx
│   └── ui/                  # shadcn UI components
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── models/         # Pydantic schemas
│   └── requirements.txt     # Python dependencies
└── README.md                # Full documentation
```

## Environment Variables

Create `.env.local` in project root:

```
BACKEND_URL=http://localhost:8000
```

## API Endpoints

### Text Analysis
```bash
curl -X POST http://localhost:8000/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text":"Click here immediately!"}'
```

### Audio Analysis
```bash
curl -X POST http://localhost:8000/api/analyze-audio \
  -F "file=@/path/to/audio.wav"
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Try reinstalling dependencies
cd backend
rm -rf venv/
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend won't start
```bash
# Clear cache and reinstall
rm -rf node_modules .next
pnpm install
pnpm dev
```

### API connection fails
1. Ensure backend is running on port 8000
2. Check `BACKEND_URL` in `.env.local`
3. Verify CORS isn't blocked (check browser console)

### Whisper model download fails
```bash
# Download model manually
python -c "import whisper; whisper.load_model('base')"
```

## Next Steps

1. **Explore the Dashboard**: Test text and audio analysis
2. **Read Full Docs**: See `README.md` for detailed documentation
3. **Deploy**: Follow `DEPLOYMENT.md` for production deployment
4. **Test**: See `TESTING.md` for testing guidelines

## Key Features Demonstrated

✅ **Text Analysis**
- Keyword-based scam detection
- Phishing pattern recognition
- Risk scoring with explanations

✅ **Audio Analysis**
- Speech-to-text transcription
- Deepfake voice detection
- Combined risk assessment

✅ **Modern UI**
- Responsive design
- Real-time analysis
- Risk meters and visual feedback
- Mobile-friendly interface

✅ **Privacy-First**
- No data persistence
- Temporary processing only
- Automatic file deletion

## Support

- **API Documentation**: http://localhost:8000/docs
- **Issues**: Check GitHub issues
- **Full Docs**: See README.md and DEPLOYMENT.md

## Example Workflow

1. **Landing Page**: Overview of features
2. **Dashboard**: Text or Audio tab
3. **Upload Content**: Paste message or upload audio
4. **Analysis**: Click analyze button
5. **Results**: See risk score with detailed explanation
6. **Action**: Make informed decision about the message

---

**That's it!** You now have a working TRUST.AI instance. Start protecting against scams!

For production deployment, see `DEPLOYMENT.md`.
