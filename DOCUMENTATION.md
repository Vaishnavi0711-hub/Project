# TRUST.AI Documentation Index

Complete guide to all documentation and resources for the TRUST.AI MVP.

## Quick Navigation

### Getting Started (Start Here!)
1. **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute local setup guide
   - Prerequisites
   - Installation steps
   - File structure overview
   - Example test cases
   - Troubleshooting

### Project Overview
2. **[README.md](./README.md)** - Complete project documentation
   - Feature overview
   - Architecture diagram
   - Tech stack details
   - API endpoints reference
   - Privacy & security info
   - Future enhancements

### Implementation Details
3. **[MVP_SUMMARY.md](./MVP_SUMMARY.md)** - What was built
   - Complete implementation breakdown
   - File structure details
   - Key algorithms explained
   - Risk score interpretation
   - Performance metrics
   - Success criteria

### Deployment & Operations
4. **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide
   - Step-by-step deployment to multiple platforms
   - Vercel, Railway, Fly.io, Render options
   - Environment configuration
   - Custom domain setup
   - Monitoring & logging
   - Scaling strategies
   - Cost estimation

### Quality Assurance
5. **[TESTING.md](./TESTING.md)** - Testing procedures
   - Unit tests (Jest, pytest examples)
   - Integration tests
   - Manual test scenarios
   - Performance benchmarks
   - Accessibility testing
   - CI/CD setup
   - Known issues & limitations

## File Organization

### Frontend Files
```
/app
  /page.tsx                    # Landing page (marketing)
  /layout.tsx                  # Root layout
  /globals.css                 # Design tokens & theme
  /dashboard
    /page.tsx                  # Main dashboard

/app/api
  /analyze-text/route.ts      # Text analysis endpoint
  /analyze-audio/route.ts     # Audio analysis endpoint

/components
  /MessageAnalyzer.tsx         # Text input component
  /AudioAnalyzer.tsx           # Audio upload/record component
  /ResultsPanel.tsx            # Results display component
  /ui                          # shadcn UI components (pre-installed)
```

### Backend Files
```
/backend
  /requirements.txt             # Python dependencies
  /app
    /main.py                   # FastAPI app entry point
    /routes
      /analyze_text.py         # Text analysis endpoint
      /analyze_audio.py        # Audio analysis endpoint
    /services
      /text_detector.py        # Text scam detection
      /speech_to_text.py       # Whisper integration
      /deepfake_detector.py    # Audio analysis
    /models
      /schemas.py              # Pydantic models
```

### Configuration Files
```
.env.example                   # Environment template
.env.local.example             # Local development example
package.json                   # Frontend dependencies
tsconfig.json                  # TypeScript config
tailwind.config.ts             # Tailwind CSS config
next.config.mjs                # Next.js configuration
backend/requirements.txt       # Python dependencies
```

### Documentation Files
```
README.md                      # Main documentation
QUICKSTART.md                  # 5-minute setup
DEPLOYMENT.md                  # Production deployment
TESTING.md                     # Testing guide
MVP_SUMMARY.md                 # Implementation details
DOCUMENTATION.md               # This file
```

## By User Role

### For Developers
1. Start: [QUICKSTART.md](./QUICKSTART.md) - Get it running locally
2. Understand: [MVP_SUMMARY.md](./MVP_SUMMARY.md) - See what was built
3. Code: [README.md](./README.md) - API reference & architecture
4. Test: [TESTING.md](./TESTING.md) - Testing procedures

### For DevOps/Deployment
1. Read: [DEPLOYMENT.md](./DEPLOYMENT.md) - All deployment options
2. Choose: Select platform (Vercel, Railway, Fly.io, Render, etc.)
3. Configure: Follow step-by-step guide for your platform
4. Monitor: Set up logging and monitoring
5. Scale: Review scaling strategies if needed

### For QA/Testers
1. Setup: [QUICKSTART.md](./QUICKSTART.md) - Get local instance running
2. Test: [TESTING.md](./TESTING.md) - Manual test scenarios
3. Verify: Test all features and edge cases
4. Report: Document bugs and issues

### For Hackathon Judges
1. Overview: [MVP_SUMMARY.md](./MVP_SUMMARY.md) - What was built
2. Features: [README.md](./README.md) - Feature list & screenshots
3. Architecture: [README.md](./README.md#architecture) - System design
4. Try It: [QUICKSTART.md](./QUICKSTART.md) - Run locally in 5 minutes

## Key Features to Explore

### Text Analysis
- Example file: `components/MessageAnalyzer.tsx`
- Backend: `backend/app/services/text_detector.py`
- Test with examples: Dashboard → "Text Messages" tab → Click example buttons

### Audio Analysis
- Example file: `components/AudioAnalyzer.tsx`
- Backend: `backend/app/services/speech_to_text.py`, `deepfake_detector.py`
- Test with recording: Dashboard → "Audio Calls" tab → Record audio

### Risk Scoring
- Display: `components/ResultsPanel.tsx`
- Algorithm: Text detection (40%) + Audio features (30%) + Sentiment (30%)
- Interpretation: Low (0-30%), Medium (30-70%), High (70-100%)

## API Reference

### Available Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/analyze-text` | POST | Analyze text for scams | Risk score, threats, explanation |
| `/api/analyze-audio` | POST | Analyze audio file | Risk score, threats, transcription |
| `/health` | GET | Health check | Service status |
| `/docs` | GET | Swagger API docs | Interactive API documentation |

See [README.md](./README.md#api-endpoints) for detailed examples.

## Environment Setup

### Local Development
```bash
# Frontend
BACKEND_URL=http://localhost:8000

# Backend (no special env vars needed for MVP)
# Optional: LOG_LEVEL=DEBUG
```

### Production (Vercel + Railway example)
```bash
# Frontend (.env.local)
BACKEND_URL=https://trust-ai-backend.railway.app

# Backend (Railway environment variables)
# Auto-configured by platform
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for platform-specific setup.

## Common Commands

### Frontend
```bash
pnpm install          # Install dependencies
pnpm dev             # Start dev server
pnpm build           # Production build
pnpm test            # Run tests
pnpm lint            # Run linter
```

### Backend
```bash
pip install -r requirements.txt  # Install dependencies
python -m uvicorn app.main:app --reload  # Start server
pytest                           # Run tests
python -m uvicorn app.main:app   # Production server
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Backend won't start | Check Python 3.10+, reinstall requirements.txt |
| Frontend can't connect to backend | Verify BACKEND_URL in .env.local |
| Audio recording doesn't work | Check browser permissions, use HTTPS |
| Whisper model too large | Use smaller model (base instead of large) |
| Port already in use | Kill process or use different port |

See [QUICKSTART.md](./QUICKSTART.md#troubleshooting) for detailed solutions.

## Performance & Optimization

- Text analysis target: < 500ms
- Audio transcription: 2-10 seconds
- API response time: < 1 second
- See [TESTING.md](./TESTING.md#performance-testing) for benchmarking

## Security Considerations

### Built-in
- Input validation (Pydantic)
- CORS configuration
- No data persistence
- HTTPS ready
- Environment variable protection

### Recommended for Production
- Rate limiting
- API authentication
- WAF (Web Application Firewall)
- Security headers
- Regular dependency updates

See [DEPLOYMENT.md](./DEPLOYMENT.md) for security best practices.

## Monitoring & Debugging

### Frontend Logs
```bash
# Enable debug logging
DEBUG=trust-ai:* pnpm dev

# Chrome DevTools
# - Console tab for errors
# - Network tab for API calls
# - React DevTools for component state
```

### Backend Logs
```bash
# Enable debug level
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload --log-level debug

# Check API docs
curl http://localhost:8000/docs
```

## Database (Future Enhancement)

Current MVP has no database. For future versions:
- Use Supabase (PostgreSQL)
- Or: Self-hosted PostgreSQL
- Or: MongoDB for document storage

Migrations would go in `backend/migrations/`

## Adding Features

### New API Endpoint
1. Create route in `backend/app/routes/`
2. Create service in `backend/app/services/`
3. Add Pydantic schema in `backend/app/models/`
4. Test with pytest
5. Expose in `backend/app/main.py`

### New Frontend Page
1. Create page in `app/[page]/page.tsx`
2. Create components in `components/`
3. Add navigation in landing page or layout
4. Style with Tailwind classes
5. Test responsiveness

## Resources & References

### Official Documentation
- [Next.js 16 Docs](https://nextjs.org/docs)
- [React 19 Docs](https://react.dev)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Tailwind CSS](https://tailwindcss.com)
- [shadcn/ui](https://ui.shadcn.com)

### AI/ML
- [OpenAI Whisper](https://github.com/openai/whisper)
- [librosa Documentation](https://librosa.org)
- [Pydantic](https://docs.pydantic.dev)

### Deployment
- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Fly.io Docs](https://fly.io/docs)

## Contributing

1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Commit: `git commit -am "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Create Pull Request

## License

MIT License - See LICENSE file

## Support

- Check [QUICKSTART.md](./QUICKSTART.md) first
- Read relevant doc from list above
- Check GitHub issues
- Contact development team

## Version History

### v1.0.0 (Current)
- Complete MVP implementation
- Text and audio analysis
- Frontend + Backend
- Full documentation
- Production deployment guides

---

**Last Updated**: 2026
**Status**: Ready for Production
**Hackathon Status**: MVP Complete

Start with [QUICKSTART.md](./QUICKSTART.md) to get running in 5 minutes!
