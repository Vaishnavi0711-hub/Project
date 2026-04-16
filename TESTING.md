# TRUST.AI Testing Guide

Complete testing guide for the TRUST.AI MVP including unit tests, integration tests, and manual testing procedures.

## Testing Overview

- **Frontend Tests**: React component tests with Jest
- **Backend Tests**: FastAPI endpoint tests with pytest
- **Integration Tests**: End-to-end API tests
- **Manual Tests**: User workflow testing
- **Performance Tests**: Load testing and benchmarks

## Setup

### Frontend Testing

Install test dependencies:
```bash
pnpm add -D @testing-library/react @testing-library/jest-dom jest @types/jest
```

Create `jest.config.js`:
```javascript
module.exports = {
  preset: 'next/jest',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
}
```

### Backend Testing

Install test dependencies:
```bash
cd backend
pip install pytest pytest-asyncio httpx
```

## Unit Tests

### Frontend Component Tests

Create `components/__tests__/MessageAnalyzer.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import MessageAnalyzer from '@/components/MessageAnalyzer'

describe('MessageAnalyzer', () => {
  it('renders input textarea', () => {
    const mockOnAnalyze = jest.fn()
    render(<MessageAnalyzer onAnalyze={mockOnAnalyze} isLoading={false} />)
    
    expect(screen.getByPlaceholderText(/Paste a suspicious message/i)).toBeInTheDocument()
  })

  it('disables analyze button when text is empty', () => {
    const mockOnAnalyze = jest.fn()
    render(<MessageAnalyzer onAnalyze={mockOnAnalyze} isLoading={false} />)
    
    const button = screen.getByRole('button', { name: /Analyze Message/i })
    expect(button).toBeDisabled()
  })

  it('calls onAnalyze when analyze button is clicked', () => {
    const mockOnAnalyze = jest.fn()
    const { getByPlaceholderText, getByRole } = render(
      <MessageAnalyzer onAnalyze={mockOnAnalyze} isLoading={false} />
    )
    
    fireEvent.change(getByPlaceholderText(/Paste a suspicious message/i), {
      target: { value: 'Click here immediately' }
    })
    
    fireEvent.click(getByRole('button', { name: /Analyze Message/i }))
    
    expect(mockOnAnalyze).toHaveBeenCalledWith('Click here immediately')
  })
})
```

### Backend Service Tests

Create `backend/tests/test_text_detector.py`:

```python
import pytest
from app.services.text_detector import TextScamDetector

@pytest.fixture
def detector():
    return TextScamDetector()

def test_urgency_keywords_detection(detector):
    """Test detection of urgency keywords"""
    result = detector.analyze("Click here immediately!")
    assert result['risk_score'] > 0
    assert 'urgency' in result['threat_types']

def test_phishing_detection(detector):
    """Test phishing pattern detection"""
    result = detector.analyze("Verify your PayPal account now at http://paypal-fake.com")
    assert result['risk_score'] > 50
    assert 'phishing' in result['threat_types']

def test_safe_message(detector):
    """Test that safe messages have low risk"""
    result = detector.analyze("Hi, how are you doing today?")
    assert result['risk_score'] < 30
    assert len(result['threat_types']) == 0

def test_multiple_threats(detector):
    """Test detection of multiple threat indicators"""
    result = detector.analyze(
        "URGENT! Verify your SSN immediately or your account will be suspended! "
        "Wire money to this account NOW!"
    )
    assert result['risk_score'] > 70
    assert len(result['threat_types']) > 1
```

## Integration Tests

### Text Analysis API Test

Create `backend/tests/test_api_text.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_text_analysis_endpoint():
    """Test text analysis endpoint"""
    response = client.post(
        "/api/analyze-text",
        json={"text": "Click here immediately to verify your account!"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "threat_types" in data
    assert "explanation" in data
    assert "confidence" in data
    assert 0 <= data["risk_score"] <= 100
    assert isinstance(data["threat_types"], list)
    assert isinstance(data["confidence"], float)

def test_text_analysis_invalid_input():
    """Test error handling for invalid input"""
    response = client.post(
        "/api/analyze-text",
        json={"text": ""}
    )
    
    assert response.status_code == 400

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### Audio Analysis API Test

Create `backend/tests/test_api_audio.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

def test_audio_analysis_invalid_file():
    """Test error handling for invalid file type"""
    response = client.post(
        "/api/analyze-audio",
        files={"file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}
    )
    
    assert response.status_code == 400

def test_audio_analysis_missing_file():
    """Test error handling for missing file"""
    response = client.post(
        "/api/analyze-audio"
    )
    
    assert response.status_code == 422  # Validation error
```

## Manual Testing Scenarios

### Test Case 1: Low-Risk Message
**Input**: "Hi, how are you doing today?"
**Expected**: Risk Score < 30%, No threats

**Steps**:
1. Go to Dashboard
2. Paste message
3. Click Analyze
4. Verify risk meter shows green
5. Verify explanation indicates safe message

### Test Case 2: High-Risk Phishing
**Input**: "URGENT! Click here immediately to verify your PayPal account or it will be suspended! http://paypal-verify.com"
**Expected**: Risk Score > 70%, Multiple threats detected

**Steps**:
1. Go to Dashboard
2. Paste message
3. Click Analyze
4. Verify risk meter shows red
5. Verify phishing_attempt threat detected
6. Verify explanation is clear

### Test Case 3: Medium-Risk Message
**Input**: "Your account has been locked. Please confirm your identity."
**Expected**: Risk Score 30-70%, 1-2 threats

**Steps**:
1. Go to Dashboard
2. Paste message
3. Click Analyze
4. Verify risk meter shows yellow
5. Verify identity_theft threat detected

### Test Case 4: Audio File Upload
**Input**: Upload an audio file
**Expected**: Transcription shown, risk score calculated

**Steps**:
1. Go to Dashboard
2. Click "Audio Calls" tab
3. Upload or record audio
4. Click Analyze
5. Verify transcription appears
6. Verify risk score is displayed

### Test Case 5: Example Messages
**Steps**:
1. Go to Dashboard
2. Click on example scam buttons
3. Verify message is pasted
4. Click Analyze
5. Verify high-risk score for scam examples

## Performance Testing

### Response Time Benchmarks

- Text analysis: < 500ms
- Audio transcription: 2-10s (file dependent)
- Total audio analysis: < 15s

Test with Apache Bench:
```bash
ab -n 100 -c 10 -p data.json -T application/json http://localhost:8000/api/analyze-text
```

### Load Testing with Locust

Create `backend/tests/locustfile.py`:

```python
from locust import HttpUser, task, between
import json

class TrustAIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def text_analysis(self):
        payload = {
            "text": "Click here immediately to verify your account!"
        }
        self.client.post("/api/analyze-text", json=payload)
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
```

Run tests:
```bash
locust -f backend/tests/locustfile.py --host=http://localhost:8000 -u 50 -r 5
```

## Accessibility Testing

### Keyboard Navigation
- [ ] All buttons and links are keyboard accessible
- [ ] Tab order is logical
- [ ] Enter key works to submit forms

### Screen Reader Testing
- [ ] Use NVDA or JAWS to test
- [ ] Verify all images have alt text
- [ ] Verify form labels are associated

### Color Contrast
- [ ] Use WAVE extension to check contrast
- [ ] Verify WCAG AA compliance
- [ ] Test with colorblind simulator

## Browser Compatibility Testing

Test on:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

## Cross-Browser Testing Services

Use BrowserStack or Sauce Labs:
```bash
npm install -g wdio @wdio/cli
wdio config
wdio run
```

## Test Coverage

Generate coverage reports:

**Frontend**:
```bash
pnpm test -- --coverage
```

**Backend**:
```bash
cd backend
pytest --cov=app tests/
```

Coverage targets:
- Statements: > 80%
- Branches: > 75%
- Functions: > 80%
- Lines: > 80%

## Continuous Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: pnpm install
      - run: pnpm test
      - run: pnpm lint

  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest
```

## Known Issues & Limitations

1. **Whisper Model Size**: Large model (2.9GB) may take time to download
2. **Audio File Size**: Limited to 25MB
3. **Mock Data**: Backend returns simulated results when Whisper unavailable
4. **CORS**: May need adjustment for production domains
5. **Rate Limiting**: Not implemented in MVP

## Testing Checklist

### Before Release
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No console errors in browser
- [ ] No TypeScript compilation errors
- [ ] Performance benchmarks met
- [ ] Accessibility tests pass
- [ ] Mobile responsiveness verified
- [ ] Cross-browser testing completed
- [ ] Security headers configured
- [ ] Environment variables set correctly

### After Deployment
- [ ] Health check endpoint working
- [ ] Frontend loads without errors
- [ ] API endpoints responding
- [ ] Error logging configured
- [ ] Monitoring active
- [ ] Rollback procedure tested

## Debugging

### Frontend Debugging
```bash
# Enable debug mode
DEBUG=* pnpm dev

# Test API calls
curl -X POST http://localhost:3000/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'
```

### Backend Debugging
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload --log-level debug

# Test endpoint directly
curl -X POST http://localhost:8000/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'
```

## Performance Profiling

### Frontend
```bash
# React DevTools Profiler
# Chrome DevTools Performance tab
pnpm build --analyze
```

### Backend
```python
# Use Python profiler
python -m cProfile -s cumulative app/main.py
```

---

Run tests before each deployment to ensure MVP quality!
