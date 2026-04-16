# Trust.AI - Complete System Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRUST.AI FRONTEND (Next.js)                          │
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐  │
│  │   Landing Page       │  │  Dashboard Interface │  │ Results Display │  │
│  │                      │  │  ┌──────────────────┐│  │ ┌─────────────┐ │  │
│  │  • Features          │  │  │ Text Input       ││  │ │ Risk Meter  │ │  │
│  │  • How it works      │  │  │ Audio Upload     ││  │ │ Threats     │ │  │
│  │  • Privacy info      │  │  │ Recording        ││  │ │ Explanation │ │  │
│  │  • Call to action    │  │  │ Examples         ││  │ │ Feedback UI │ │  │
│  │                      │  │  │ [Analysis]       ││  │ │ (NEW!)      │ │  │
│  │                      │  │  └──────────────────┘│  │ └─────────────┘ │  │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘  │
│                                      │                                      │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                HTTP/JSON API          │
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                      TRUST.AI BACKEND (FastAPI)                            │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         REQUEST HANDLING                             │  │
│  │  ┌──────────────────┐        ┌──────────────────┐                   │  │
│  │  │ /api/analyze-text│        │/api/analyze-audio│                   │  │
│  │  │                  │        │                  │                   │  │
│  │  │ • Validation     │        │ • File upload    │                   │  │
│  │  │ • Routing        │        │ • Size check     │                   │  │
│  │  │ • Cleanup        │        │ • Routing        │                   │  │
│  │  └──────────────────┘        └──────────────────┘                   │  │
│  │           │                           │                             │  │
│  └───────────┼───────────────────────────┼─────────────────────────────┘  │
│              │                           │                                 │
│  ┌───────────▼───────────────────────────▼──────────────────────────────┐  │
│  │                        ANALYSIS SERVICES                            │  │
│  │                                                                      │  │
│  │  ┌─────────────────────────┐    ┌──────────────────────────────┐   │  │
│  │  │  TEXT ANALYSIS          │    │  AUDIO ANALYSIS PIPELINE     │   │  │
│  │  │  (text_detector.py)     │    │  (analyze_audio.py)          │   │  │
│  │  │                         │    │                              │   │  │
│  │  │ • Keyword detection     │    │ 1. Speech-to-Text           │   │  │
│  │  │ • Pattern matching      │    │    (speech_to_text.py)      │   │  │
│  │  │ • URL analysis          │    │    • Whisper API            │   │  │
│  │  │ • Threat categorization │    │    • Transcription          │   │  │
│  │  │ • Risk scoring (0-100)  │    │                              │   │  │
│  │  │ • Confidence metrics    │    │ 2. Text Analysis            │   │  │
│  │  │                         │    │    (text_detector.py)       │   │  │
│  │  │ Response:              │    │    • Same as text analysis   │   │  │
│  │  │ • risk_score           │    │                              │   │  │
│  │  │ • threats              │    │ 3. Deepfake Detection (NEW!) │   │  │
│  │  │ • explanation          │    │    • Try CNN first           │   │  │
│  │  │ • confidence           │    │    • Fall back to heuristic  │   │  │
│  │  │                         │    │                              │   │  │
│  │  │                         │    │ 4. Combine Results          │   │  │
│  │  │                         │    │    • Weighted scoring       │   │  │
│  │  │                         │    │    • Merge threats          │   │  │
│  │  │                         │    │    • Final risk score       │   │  │
│  │  └─────────────────────────┘    └──────────────────────────────┘   │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                   DEEPFAKE DETECTION (NEW!)                         │  │
│  │                                                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │  CNN DEEPFAKE DETECTOR (cnn_deepfake_detector.py)           │   │  │
│  │  │  ✓ Async inference   ✓ Variable length   ✓ Fallback         │   │  │
│  │  │                                                              │   │  │
│  │  │  • Load mel-spectrogram                                     │   │  │
│  │  │  • Normalize & process                                     │   │  │
│  │  │  • Forward through CNN                                     │   │  │
│  │  │  • Get deepfake probability                               │   │  │
│  │  │  • Convert to risk score                                  │   │  │
│  │  │  • Return results                                         │   │  │
│  │  │                                                              │   │  │
│  │  │  Falls back to HEURISTIC if:                                │   │  │
│  │  │  • Model not loaded                                         │   │  │
│  │  │  • Error occurs                                             │   │  │
│  │  │  • Feature extraction fails                                │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │  MODEL LAYER (app/models/)                                   │   │  │
│  │  │                                                              │   │  │
│  │  │  ┌────────────────────────────────────────────────────────┐ │   │  │
│  │  │  │ DeepfakeCNN (Standard)                                 │ │   │  │
│  │  │  │ • 4 Conv Blocks • 256 filters • 2.2M params           │ │   │  │
│  │  │  │ • 200ms inference • 90-95% accuracy                    │ │   │  │
│  │  │  └────────────────────────────────────────────────────────┘ │   │  │
│  │  │                   OR (for fast inference)                     │   │  │
│  │  │  ┌────────────────────────────────────────────────────────┐ │   │  │
│  │  │  │ LightweightDeepfakeCNN                                 │ │   │  │
│  │  │  │ • 3 Conv Blocks • 64 filters • 65K params              │ │   │  │
│  │  │  │ • 50ms inference • 85-90% accuracy                     │ │   │  │
│  │  │  └────────────────────────────────────────────────────────┘ │   │  │
│  │  │                                                              │   │  │
│  │  │  Trained weight checkpoint: models/cnn_deepfake_best.pt    │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                  ONLINE LEARNING (NEW!)                            │  │
│  │                   (services/online_learning.py)                    │  │
│  │                                                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │ User Feedback Flow:                                          │   │  │
│  │  │                                                              │   │  │
│  │  │ User: "Was this correct?" ──→ Submit Audio                 │   │  │
│  │  │                                           │                 │   │  │
│  │  │              ┌────────────────────────────▼──────────────┐   │  │
│  │  │              │ Online Learning Service                   │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ 1. Confidence Check                       │   │  │
│  │  │              │    (skip if >70% confident & correct)     │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ 2. Feature Extraction                     │   │  │
│  │  │              │    (mel-spectrogram normalization)        │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ 3. Secure Deletion (DoD 5220.22-M)        │   │  │
│  │  │              │    • Overwrite with zeros                 │   │  │
│  │  │              │    • Overwrite with ones                  │   │  │
│  │  │              │    • Overwrite with random                │   │  │
│  │  │              │    • Delete file                          │   │  │
│  │  │              │    • Verify deletion                      │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ 4. Buffer Accumulation                    │   │  │
│  │  │              │    (group samples for stable training)    │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ 5. Model Training (if buffer full)        │   │  │
│  │  │              │    • EWC regularization                   │   │  │
│  │  │              │    • Low learning rate (1e-5)             │   │  │
│  │  │              │    • Gradient clipping                    │   │  │
│  │  │              │    • Multi-epoch training                 │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ 6. Checkpoint Management                  │   │  │
│  │  │              │    • Save trained model                   │   │  │
│  │  │              │    • Version tracking                     │   │  │
│  │  │              │    • Rollback capability                  │   │  │
│  │  │              │                                           │   │  │
│  │  │              │ Response: {                               │   │  │
│  │  │              │   success: true,                          │   │  │
│  │  │              │   data_deleted: true,                     │   │  │
│  │  │              │   model_version: 5,                       │   │  │
│  │  │              │   training_loss: 0.34                     │   │  │
│  │  │              │ }                                         │   │  │
│  │  │              └────────────────────────────────────────┘   │   │  │
│  │  │                                                              │   │  │
│  │  │ Key Components:                                              │   │  │
│  │  │ • SecureDeletion: 3-pass overwrite + verification          │   │  │
│  │  │ • EWC: Prevent catastrophic forgetting                     │   │  │
│  │  │ • Confidence Sampling: Avoid data poisoning                │   │  │
│  │  │ • Checkpoint Manager: Auto-rollback on failure             │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  │  API Endpoints (routes/feedback.py):                                │  │
│  │  • POST /api/feedback/audio - Submit feedback                       │  │
│  │  • GET /api/feedback/status - Training status                       │  │
│  │  • POST /api/feedback/flush - Force training                        │  │
│  │  • GET /api/health/learning - Service health                        │  │
│  │                                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Text Analysis
```
User Input (Text)
    ↓
Validation
    ↓
TextScamDetector.analyze()
    ├── Keyword extraction
    ├── Pattern matching
    ├── URL analysis
    ├── Risk scoring
    └── Confidence calculation
    ↓
Response {risk_score, threats, explanation, confidence}
    ↓
Frontend Display
```

### Audio Analysis
```
User Input (Audio File)
    ↓
Validation (type, size)
    ↓
Save Temp File
    ↓
Speech-to-Text (Whisper)
    ├── Load audio
    ├── Transcribe
    └── Return text
    ↓
Text Analysis (same as above)
    ↓
Audio Analysis (CNN or Heuristic)
    ├── Load audio
    ├── Extract mel-spectrogram
    ├── Forward through CNN
    ├── Get deepfake probability
    └── Return risk score
    ↓
Combine Results (60% text, 40% audio)
    ↓
Cleanup (Delete temp file)
    ↓
Response {risk_score, threats, transcription, confidence, model_type}
    ↓
Frontend Display
```

### Online Learning Flow
```
Analysis Complete
    ↓
Display Results
    ↓
User Feedback ("Was this correct?")
    ├── Yes: correct_label=0
    └── No: correct_label=1
    ↓
POST /api/feedback/audio {file, correct_label, model_prediction}
    ↓
Check Confidence
    ├── If >70% confident AND correct → Skip learning
    └── Otherwise → Learn
    ↓
Extract Features (mel-spectrogram)
    ↓
Secure Delete Audio (DoD 5220.22-M)
    ├── Overwrite 3 times
    ├── Delete file
    └── Verify deletion
    ↓
Add to Training Buffer
    ↓
If Buffer Full (4 samples)
    ├── Train Model
    │   ├── Apply EWC regularization
    │   ├── Low learning rate (1e-5)
    │   ├── Gradient clipping
    │   └── Multi-epoch training
    ├── Save Checkpoint
    └── Update Version
    ↓
Response {success, data_deleted, model_version, training_loss}
    ↓
Model Improves Continuously
```

## Component Interactions

```
Frontend                  Next.js Routes              Backend Services
   ↓                           ↓                            ↓
[Landing]  ─────────────────────────────────────────────────
[Dashboard] ← Text Input ──→ /api/analyze-text ──→ TextScamDetector
             ← Audio File ──→ /api/analyze-audio → SpeechToText
                                                  ↓ AudioAnalyzer
                                                  ├─ TextScamDetector
                                                  └─ DeepfakeDetector
                                                     (CNN + Heuristic)
[Results]   ← Analysis Result ←──────────────────────────
             ← Display Feedback UI                        
             ← Feedback Button ──→ /api/feedback/audio ──→ OnlineLearning
                                       ↓
                                    Extract Features
                                    Delete Audio
                                    Update Model
                                       ↓
             ← Success Response ────────┴────────────────
```

## Model Architecture

### CNN for Deepfake Detection

```
Input: Mel-Spectrogram
(1 channel, 128 bins, variable time steps)
    ↓
Adaptive Global Average Pooling
(handles variable input sizes)
    ↓
Conv Block 1  → Conv(1→32)  → Batch Norm → ReLU → MaxPool(2x2)
    ↓
Conv Block 2  → Conv(32→64) → Batch Norm → ReLU → MaxPool(2x2)
    ↓
Conv Block 3  → Conv(64→128) → Batch Norm → ReLU → MaxPool(2x2)
    ↓
Conv Block 4  → Conv(128→256) → Batch Norm → ReLU → MaxPool(2x2)
    ↓
Global Average Pooling
    ↓
FC Layer 1  → Linear(256→128) → ReLU → Dropout(0.5)
    ↓
FC Layer 2  → Linear(128→64) → ReLU → Dropout(0.5)
    ↓
Output Layer → Linear(64→1) → Sigmoid
    ↓
Output: Probability [0, 1]
(0 = real, 1 = deepfake)
```

## Deployment Architecture

```
Internet
    ↓
CDN (Static Assets)
    ↓
┌────────────────────────────────────────┐
│        Frontend Container              │
│  • Next.js Production Server           │
│  • Nginx Reverse Proxy                 │
│  • Port: 3000                          │
└────────────────────────────────────────┘
    ↓
Application Network
    ↓
┌────────────────────────────────────────┐
│        Backend Container               │
│  • FastAPI Application                 │
│  • Uvicorn ASGI Server                 │
│  • Port: 8000                          │
│                                        │
│  • Text Detection                      │
│  • Audio Processing                    │
│  • CNN Inference (optional GPU)        │
│  • Online Learning                     │
└────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────┐
│        Storage                         │
│  • Model Checkpoints (models/)         │
│  • Training Data (training/data/)      │
│  • Logs                                │
└────────────────────────────────────────┘
```

---

**This architecture enables:**
✅ Scalability - All components can be containerized  
✅ Privacy - No data persistence between requests  
✅ Reliability - Fallbacks at each stage  
✅ Improvement - Online learning continuously refines models  
✅ Transparency - Clear data flow and responsibility  
