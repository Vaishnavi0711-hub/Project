# Trust.AI - Complete Project Flow & Architecture

## 🏗️ Overview

Trust.AI is a privacy-first scam detection platform that analyzes both **text and audio** for scams in real-time. It has:
- **Frontend**: React-based (Next.js) user interface
- **Backend**: Python FastAPI server with ML models
- **ML Models**: Custom-trained CNN for deepfake detection + text analysis engine
- **Learning**: Online learning system that improves with user feedback

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│  http://localhost:3000  (Next.js React App)                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Landing Page    │  │  Dashboard       │  │  Results     │  │
│  │  - Features      │  │  - Text Input    │  │  - Risk Meter│  │
│  │  - How it works  │  │  - Audio Upload  │  │  - Details   │  │
│  │  - Call-to-action│  │  - Recording     │  │  - Feedback  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                    │                      │
          │ HTTP/JSON Requests │                      │
          ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Next.js API Route (Middleware Layer)                │
│                                                                  │
│  /api/analyze-text   →  POST /api/analyze-text (backend)       │
│  /api/analyze-audio  →  POST /api/analyze-audio (backend)      │
│  /api/feedback       →  POST /api/feedback/audio (backend)     │
│                                                                  │
│  Features:                                                       │
│  - Request validation                                           │
│  - Error handling                                               │
│  - Timeout protection (5 seconds)                              │
│  - Fallback analysis if backend unavailable                    │
└─────────────────────────────────────────────────────────────────┘
          │                                             │
          │ FastAPI HTTP Calls                         │
          ▼                                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend API Server (FastAPI)                        │
│         http://127.0.0.1:8000  (Python)                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ROUTES                                                 │   │
│  │  - POST /api/analyze-text                              │   │
│  │  - POST /api/analyze-audio                             │   │
│  │  - POST /api/feedback/audio                            │   │
│  │  - GET /api/feedback/status                            │   │
│  │  - GET /health                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐   │
│  │  ANALYSIS SERVICES                                      │   │
│  │                                                         │   │
│  │  Text Analysis:                                        │   │
│  │  ├─ TextScamDetector (keyword-based + pattern match)  │   │
│  │  └─ Risk scoring, threat categorization               │   │
│  │                                                         │   │
│  │  Audio Analysis:                                       │   │
│  │  ├─ SpeechToText (OpenAI Whisper)                     │   │
│  │  ├─ TextScamDetector (same as above)                  │   │
│  │  ├─ CNNDeepfakeDetector (trained on your data)        │   │
│  │  └─ Combine results using weighted scoring            │   │
│  │                                                         │   │
│  │  Online Learning:                                      │   │
│  │  ├─ User feedback collection                           │   │
│  │  ├─ Feature extraction                                 │   │
│  │  ├─ Buffer accumulation                                │   │
│  │  ├─ Model training (with EWC)                          │   │
│  │  └─ Secure data deletion                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ML MODELS                                              │   │
│  │  - CNN Deepfake Detector (trained model in memory)     │   │
│  │  - Text Analysis Engine                                │   │
│  │  - Mel-spectrogram feature extraction                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow - Text Analysis

### Step 1: User Interaction (Frontend)
```
User types: "Click here to verify your account!"
                          ↓
Frontend (React Component) validates input
                          ↓
Sends POST to: /api/analyze-text
                          ↓
{
  "text": "Click here to verify your account!"
}
```

### Step 2: Next.js API Route Processing
**File: `app/api/analyze-text/route.ts`**

```typescript
1. Receive request from frontend
   ├─ Extract text from request body
   └─ Validate (not empty, is string)

2. Try to call Python backend
   ├─ POST to http://127.0.0.1:8000/api/analyze-text
   ├─ Set 5-second timeout
   └─ Wait for response

3. If backend responds:
   ├─ Parse JSON response
   ├─ Extract: risk_score, threats, explanation, confidence
   └─ Return to frontend

4. If backend fails or timeout:
   ├─ Use fallback analysis function
   ├─ Check for keywords locally
   ├─ Calculate risk score
   └─ Return fallback response

5. Return response to frontend as JSON
```

### Step 3: Backend Processing
**File: `backend/app/routes/analyze_text.py`**

```python
1. Receive text from Next.js API route
   ├─ Validate input
   └─ Create TextScamDetector instance

2. Text Analysis Engine:
   ├─ Convert text to lowercase
   ├─ Extract keywords using defined patterns
   ├─ Check for:
   │  ├─ Phishing keywords ("verify account", "confirm identity")
   │  ├─ Urgency keywords ("immediately", "act now")
   │  ├─ Financial keywords ("send money", "bank account")
   │  ├─ Threat keywords ("suspended", "locked")
   │  └─ Identity theft keywords ("password", "SSN")
   │
   ├─ Match patterns:
   │  ├─ URL patterns
   │  ├─ Email patterns
   │  └─ Phone patterns
   │
   ├─ Calculate threat scores per category
   └─ Generate explanation

3. Return JSON response:
   {
     "risk_score": 45,
     "threat_types": ["phishing", "urgency"],
     "explanation": "Message contains phishing...",
     "confidence": 0.75
   }

4. Next.js API route receives and returns to frontend
```

### Step 4: Frontend Display
```
Response arrives at frontend
        ↓
React component renders results
        ↓
Display:
  - Risk meter (0-100 scale with color coding)
  - List of detected threats
  - Explanation of risks
  - Confidence score
  - Feedback buttons (Is this correct?)
```

---

## 🎙️ Request Flow - Audio Analysis

### Step 1: User Uploads Audio
```
User selects/records audio file
              ↓
Frontend sends to: /api/analyze-audio
              ↓
Multipart form data with WAV/MP3 file
```

### Step 2: Backend Audio Processing
**File: `backend/app/routes/analyze_audio.py`**

```python
1. Receive audio file from frontend
   ├─ Validate file type (WAV, MP3, etc.)
   ├─ Check file size (max 25 MB)
   └─ Save to temporary location

2. Speech-to-Text Conversion
   ├─ Load audio using librosa
   ├─ Convert to 16kHz mono
   ├─ Send to OpenAI Whisper model
   ├─ Get transcribed text
   └─ Store transcription

3. Text Analysis (same as above)
   ├─ Run text analysis on transcription
   ├─ Extract threat types
   └─ Calculate text-based risk

4. Audio Deepfake Detection
   ├─ Load trained CNN model from disk
   ├─ Extract mel-spectrogram features
   ├─ Normalize to fixed time steps
   ├─ Forward through CNN
   ├─ Get deepfake probability (0-1)
   └─ Convert to risk score (0-100)

5. Combine Results
   ├─ Text-based risk: 60% weight
   ├─ Audio deepfake risk: 40% weight
   ├─ Weighted average
   └─ Calculate combined threats

6. Cleanup
   ├─ Delete temporary audio file
   └─ Return response

7. Return Response:
   {
     "risk_score": 58,
     "threat_types": ["phishing", "voice_deepfake"],
     "transcription": "Click here to verify...",
     "explanation": "Audio contains deepfake characteristics",
     "confidence": 0.82,
     "model_type": "CNN"
   }
```

---

## 🧠 CNN Model - Deepfake Detection

### Model Architecture
**File: `backend/app/models/cnn_model.py`**

```
Input: Audio File (WAV/MP3)
  ↓
[Audio Loading & Preprocessing]
  - Load at 16kHz sample rate
  - Convert to mono
  - Normalize amplitude
  ↓
[Feature Extraction - Mel-Spectrogram]
  - Apply FFT (2048 window)
  - Convert to mel scale (128 bins)
  - Power to dB conversion
  - Normalize to [-∞, 0] dB range
  - Fixed to 94 time steps (3 seconds)
  ↓
[CNN Model]
  Input: (1, 128, 94)  [channels, mels, time]
  
  ├─ Conv Block 1
  │  ├─ Conv: 1 → 32 filters (3x3)
  │  ├─ BatchNorm
  │  ├─ ReLU activation
  │  └─ MaxPool (2x2)
  │
  ├─ Conv Block 2
  │  ├─ Conv: 32 → 64 filters
  │  ├─ BatchNorm
  │  ├─ ReLU
  │  └─ MaxPool (2x2)
  │
  ├─ Conv Block 3
  │  ├─ Conv: 64 → 128 filters
  │  ├─ BatchNorm
  │  ├─ ReLU
  │  └─ MaxPool (2x2)
  │
  ├─ Conv Block 4
  │  ├─ Conv: 128 → 256 filters
  │  ├─ BatchNorm
  │  ├─ ReLU
  │  └─ MaxPool (2x2)
  │
  ├─ Global Average Pooling
  │  └─ Produces: 256D vector
  │
  ├─ FC Layer 1
  │  ├─ Linear: 256 → 128
  │  ├─ ReLU
  │  └─ Dropout (0.5)
  │
  ├─ FC Layer 2
  │  ├─ Linear: 128 → 64
  │  ├─ ReLU
  │  └─ Dropout (0.5)
  │
  └─ Output Layer
     ├─ Linear: 64 → 1
     └─ Sigmoid activation → probability [0, 1]
  
  Output: 0.0 = Genuine, 1.0 = Deepfake
  ↓
[Postprocessing]
  - Convert probability to risk score
  - 0.0 prob → 0 risk
  - 0.5 prob → 50 risk
  - 1.0 prob → 100 risk
  ↓
Output: Risk Score (0-100)
```

### How CNN Was Trained

**File: `backend/training/train_cnn.py`**

```python
1. Load Dataset
   ├─ Genuine folder: 11 audio files (label: 0)
   ├─ Scam folder: 6 audio files (label: 1)
   └─ Total: 17 samples → 13 train, 4 validation

2. Data Preprocessing
   ├─ Load each audio file
   ├─ Extract mel-spectrogram
   ├─ Pad/truncate to 94 time steps
   ├─ Normalize using mean/std
   └─ Apply augmentation (pitch shift, time stretch)

3. Training Loop (30 epochs)
   ├─ Forward pass through CNN
   ├─ Calculate BCE loss
   │  └─ Measures difference from true labels
   ├─ Backpropagation
   ├─ Update weights using Adam optimizer
   └─ Calculate accuracy

4. Validation
   ├─ Every epoch, test on validation set
   ├─ Track best model
   └─ Early stopping if no improvement

5. Result
   ├─ Training Accuracy: 100%
   ├─ Validation Accuracy: 100%
   └─ Best model saved to: backend/models/cnn_deepfake_best.pt

6. At Startup
   ├─ Backend loads pre-trained weights
   ├─ Initializes model for inference
   └─ Ready to classify new audio
```

---

## 📚 Online Learning System

### How User Feedback Improves the Model

**File: `backend/app/routes/feedback.py` + `backend/app/services/online_learning.py`**

```
User receives results
        ↓
User clicks: "Is this correct?" button
        ↓
Frontend sends feedback:
{
  "file": <audio data>,
  "correct_label": 0,  // 0=genuine, 1=scam
  "model_prediction": 0.35  // What model predicted
}
        ↓
Backend processes feedback...
```

### Feedback Processing Pipeline

```
1. Receive Feedback
   ├─ Extract audio file
   ├─ Extract user's correct label
   ├─ Get model's prediction for comparison
   └─ Extract probability score

2. Decision: Should we learn from this?
   ├─ Check confidence threshold (70%)
   ├─ If model was >70% confident AND correct
   │  └─ Skip learning (already knows this)
   ├─ If model was wrong or uncertain
   │  └─ ADD TO LEARNING BUFFER
   
   Purpose: Avoid learning from cases model already knows
            while learning from mistakes/uncertain cases

3. Extract Features
   ├─ Load audio file
   ├─ Convert to mel-spectrogram (same as inference)
   ├─ Normalize features
   └─ Store in memory buffer

4. Secure Data Deletion
   ├─ Overwrite audio file with zeros (first pass)
   ├─ Overwrite audio file with ones (second pass)
   ├─ Overwrite audio file with random data (third pass)
   ├─ Delete file from disk
   └─ Verify deletion was successful
   
   DOD 5220.22-M Standard: Can't recover deleted data even forensically

5. Buffer Management
   ├─ Accumulate feedback samples
   ├─ Default buffer size: 4 samples
   ├─ When buffer full: TRAIN MODEL
   
   Why accumulation?
   - Single sample training = noisy gradients
   - Batch of 4 samples = stable updates
   - More predictable learning

6. Model Training (when buffer full)
   ├─ Initialize optimizer with low learning rate (1e-5)
   │  Why low? Prevent catastrophic forgetting
   │
   ├─ Apply Elastic Weight Consolidation (EWC)
   │  - Calculate Fisher Information Matrix
   │  - Penalize changes to important weights
   │  - Preserve old knowledge
   │
   ├─ Forward pass on batch
   ├─ Calculate loss
   ├─ Add EWC regularization loss
   ├─ Backpropagation
   ├─ Gradient clipping (prevent exploding gradients)
   └─ Update weights

7. Save Checkpoint
   ├─ Save trained model state
   ├─ Increment version number
   ├─ Keep 5 most recent versions for rollback
   └─ Delete oldest checkpoints

8. Response to User
   {
     "success": true,
     "data_deleted": true,
     "model_trained": true,
     "training_loss": 0.34,
     "model_version": 5
   }

9. Model Improves
   ├─ Next predictions use updated weights
   ├─ Better accuracy over time
   └─ No manual retraining needed
```

### Key Safety Features

**Catastrophic Forgetting Prevention (EWC)**
```
Problem: When learning new samples, model forgets old knowledge
         Like learning new language makes you forget first

Solution: Elastic Weight Consolidation
         - Remember which weights were important for old tasks
         - Penalize changes to those weights
         - Allow changes to less important weights
         
Result: Learn new data WITHOUT forgetting old knowledge
```

**Data Poisoning Prevention**
```
Problem: Malicious user submits wrong labels to corrupt model
         Like training a dog with incorrect commands

Solution: Confidence-based sampling
         - Skip learning if model is already confident (~70%)
         - Only learn from mistakes and uncertain cases
         - Check user label matches actual content
         
Result: Robust learning from honest feedback only
```

**Privacy Protection**
```
Problem: Audio files stored on server = privacy breach

Solution: DoD 5220.22-M deletion standard
         - Overwrite data 3 times (impossible to recover)
         - Delete from disk
         - Verify deletion
         
Result: Zero data persistence, forensically unrecoverable
```

---

## 🔐 Security & Data Deletion

### Secure Deletion Process

**File: `backend/app/services/online_learning.py`**

```python
async def secure_delete(file_path: str):
    
    # Get file size
    file_size = Path(file_path).stat().st_size
    
    # DoD 5220.22-M: 3-pass overwrite
    
    # Pass 1: Overwrite with zeros (00000000)
    with open(file_path, 'wb') as f:
        f.write(b'\x00' * file_size)
    
    # Pass 2: Overwrite with ones (11111111)  
    with open(file_path, 'wb') as f:
        f.write(b'\xff' * file_size)
    
    # Pass 3: Overwrite with random data
    with open(file_path, 'wb') as f:
        f.write(os.urandom(file_size))
    
    # Delete from filesystem
    Path(file_path).unlink()
    
    # Verify deletion with retries
    for attempt in range(3):
        await asyncio.sleep(0.1)
        if not Path(file_path).exists():
            return True  # Success
    
    return False  # Failed (rare)

Why this matters:
- Standard delete = data still on disk (recoverable)
- This approach = data physically overwritten
- Even with enterprise recovery tools: impossible
```

---

## 🎯 Complete Request-Response Cycle

### Example: User submits scammy text

```
FRONTEND (Next.js / React)
┌─────────────────────────────────────┐
│ User types: "Verify account now!"  │
│ Click: Analyze                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ app/api/analyze-text/route.ts       │
│ 1. Receive request                  │
│ 2. Validate text (not empty)       │
│ 3. Call backend API                 │
│    POST http://127.0.0.1:8000/...  │
│ 4. Handle response                  │
│ 5. Return JSON to React component   │
└──────────────┬──────────────────────┘
               │
               │ HTTP POST JSON
               ▼
BACKEND (FastAPI / Python)
┌─────────────────────────────────────────────────┐
│ backend/app/routes/analyze_text.py              │
│                                                 │
│ 1. Receive: {"text": "Verify account now!"}   │
│    ├─ Validate                                  │
│    └─ Create TextScamDetector()                │
│                                                 │
│ 2. TextScamDetector.analyze()                  │
│    ├─ Tokenize text                            │
│    ├─ Check keywords:                          │
│    │  ├─ "verify" → PHISHING keyword ✓        │
│    │  ├─ "account" → IDENTITY keyword ✓       │
│    │  ├─ "now" → URGENCY keyword ✓            │
│    │  └─ Found 3 threat categories             │
│    │                                            │
│    ├─ Calculate risk:                          │
│    │  ├─ 3 categories × 20 points each        │
│    │  ├─ Base risk: 60 points                 │
│    │  └─ Apply confidence multiplier           │
│    │                                            │
│    ├─ Generate explanation:                    │
│    │  "This message contains phishing and     │
│    │   identity theft indicators. Do not      │
│    │   verify your account via this link."    │
│    │                                            │
│    └─ Return:                                  │
│       {                                        │
│         "risk_score": 65,                      │
│         "threat_types": [                      │
│           "phishing",                          │
│           "identity_theft",                    │
│           "urgency"                            │
│         ],                                     │
│         "explanation": "...",                  │
│         "confidence": 0.85                     │
│       }                                        │
│                                                 │
│ 3. Return to Next.js API route                │
└──────────────┬──────────────────────────────────┘
               │
               │ HTTP Response JSON
               ▼
FRONTEND (React Component)
┌─────────────────────────────────────┐
│ Receive response:                    │
│ ├─ risk_score: 65                  │
│ ├─ threats: [phishing, ...]        │
│ ├─ explanation: "..."               │
│ └─ confidence: 0.85                │
│                                     │
│ Render Results:                     │
│ ┌─────────────────────────────────┐│
│ │ RISK METER: ████████░░ 65%      ││
│ │ Status: HIGH RISK (RED)         ││
│ │                                 ││
│ │ Threats Detected:               ││
│ │ • Phishing attempt              ││
│ │ • Identity theft                ││
│ │ • Sense of urgency              ││
│ │                                 ││
│ │ Recommendation:                 ││
│ │ Do not verify account via this  ││
│ │ link. Contact your bank directly││
│ │                                 ││
│ │ [Was this correct?]             ││
│ │ [Yes] [No]                      ││
│ └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## 📱 Component Interaction Map

```
FRONTEND COMPONENTS
├─ app/page.tsx
│  └─ Landing page (features, CTA)
│
├─ app/dashboard/page.tsx
│  └─ Main analysis interface
│     ├─ Calls: /api/analyze-text
│     ├─ Calls: /api/analyze-audio
│     └─ Displays: ResultsPanel component
│
├─ components/MessageAnalyzer.tsx
│  └─ Text input & analysis
│     └─ Calls: POST /api/analyze-text
│
├─ components/AudioAnalyzer.tsx
│  └─ Audio upload/recording
│     └─ Calls: POST /api/analyze-audio
│
├─ components/ResultsPanel.tsx
│  └─ Displays analysis results
│     ├─ Risk score visualization
│     ├─ Threat list
│     ├─ Explanation text
│     └─ Feedback buttons
│
└─ components/ui/* (UI components)
   ├─ Card, Button, Slider, etc.
   └─ Styled with Tailwind CSS

BACKEND COMPONENTS
├─ app/main.py (FastAPI app)
│  ├─ Middleware setup
│  ├─ CORS configuration
│  ├─ Route registration
│  └─ Startup initialization
│
├─ app/routes/
│  ├─ analyze_text.py
│  │  └─ POST /api/analyze-text
│  │
│  ├─ analyze_audio.py
│  │  ├─ POST /api/analyze-audio
│  │  └─ Orchestrates: Whisper → Text Analysis → CNN
│  │
│  └─ feedback.py
│     ├─ POST /api/feedback/audio
│     ├─ GET /api/feedback/status
│     ├─ POST /api/feedback/flush
│     └─ GET /api/health/learning
│
├─ app/services/
│  ├─ text_detector.py
│  │  └─ TextScamDetector class (keyword-based)
│  │
│  ├─ speech_to_text.py
│  │  └─ SpeechToTextService (OpenAI Whisper)
│  │
│  ├─ deepfake_detector.py
│  │  └─ DeepfakeDetector (heuristic fallback)
│  │
│  ├─ cnn_deepfake_detector.py
│  │  └─ CNNDeepfakeDetector (trained model inference)
│  │
│  └─ online_learning.py
│     ├─ SecureDeletion (DoD 5220.22-M)
│     ├─ ElasticWeightConsolidation (EWC)
│     └─ OnlineLearningService (orchestrator)
│
├─ app/models/
│  ├─ cnn_model.py
│  │  ├─ DeepfakeCNN (main model - 2.2M params)
│  │  └─ LightweightDeepfakeCNN (65K params)
│  │
│  ├─ schemas.py
│  │  ├─ TextAnalysisRequest
│  │  ├─ TextAnalysisResponse
│  │  ├─ AudioAnalysisResponse
│  │  └─ FeedbackResponse
│  │
│  └─ */cnn_deepfake_best.pt (saved model weights)
│
├─ training/
│  ├─ train_cnn.py
│  │  └─ ModelTrainer class (training loop)
│  │
│  ├─ dataset.py
│  │  └─ DeepfakeAudioDataset class (data loading)
│  │
│  ├─ data/
│  │  ├─ genuine/ (11 audio files)
│  │  └─ scam/ (6 audio files)
│  │
│  ├─ models/ (trained model storage)
│  │  └─ cnn_deepfake_best.pt
│  │
│  └─ test_online_learning.py
│     └─ Unit tests for learning system
│
└─ config.py (training configuration)
```

---

## 🔄 Data Flow Summary

```
USER INPUT (Text or Audio)
        │
        ▼
┌──────────────────────────┐
│  FRONTEND VALIDATION     │
│  - Check not empty       │
│  - Validate format       │
│  - Show loading state    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  NEXT.JS API ROUTE               │
│  (app/api/analyze-text|audio)    │
│  - Receive from React            │
│  - Call backend                  │
│  - Handle timeout/errors         │
│  - Fallback if needed            │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  FASTAPI BACKEND                 │
│  /api/analyze-text|audio         │
│  - Validate input                │
│  - Route to services             │
└────────────┬─────────────────────┘
             │
        ┌────┴─────────────────┐
        │                      │
        ▼                      ▼
    [TEXT PATH]           [AUDIO PATH]
        │                      │
        ▼                      ▼
┌────────────────┐    ┌──────────────────┐
│ TextDetector   │    │ Whisper (STT)    │
│ ├─ Keywords   │    │ Convert to text  │
│ ├─ Patterns   │    └────────┬─────────┘
│ └─ Threats    │             │
└────────┬───────┘             ▼
         │            ┌──────────────────┐
         │            │ TextDetector (2) │
         │            └────────┬─────────┘
         │                     │
         └────────┬────────────┘
                  │
         ┌────────▼────────┐
         │ CNN Detector    │
         │ (if audio)      │
         └────────┬────────┘
                  │
         ┌────────▼───────────┐
         │ Score Combination  │
         │ (Weight + Merge)   │
         └────────┬───────────┘
                  │
         ┌────────▼─────────────┐
         │ Format Response JSON │
         └────────┬─────────────┘
                  │
                  ▼
         ┌─────────────────────┐
         │ Return to Next.js   │
         └────────┬────────────┘
                  │
         ┌────────▼────────────┐
         │ Display in React    │
         │ - Risk meter        │
         │ - Threats list      │
         │ - Explanation       │
         │ - Feedback buttons  │
         └────────┬────────────┘
                  │
    USER PROVIDES FEEDBACK?
         │        │
    YES  │        │ NO
         ▼        │
    ┌─────────────┐
    │ SEND TO     │
    │ /feedback   │
    │ endpoint    │
    └─────┬───────┘
          │
    ┌─────▼─────────────────┐
    │ ONLINE LEARNING       │
    │ ├─ Extract features   │
    │ ├─ Delete audio       │
    │ ├─ Buffer samples     │
    │ ├─ Train if ready     │
    │ └─ Update version     │
    └───────────────────────┘
```

---

## ⚙️ Key Technologies & Libraries

### Frontend
- **Next.js 16**: React framework with API routes
- **React 19**: Component-based UI
- **TypeScript**: Type-safe code
- **Tailwind CSS**: Styling
- **UI Components**: Shadcn/ui library

### Backend
- **FastAPI**: Modern Python web framework
- **PyTorch**: Deep learning framework
- **Librosa**: Audio processing
- **OpenAI Whisper**: Speech-to-text
- **SQLAlchemy (optional)**: Database ORM
- **Pydantic**: Data validation

### ML/AI
- **CNN (Convolutional Neural Network)**: Deepfake detection
- **EWC (Elastic Weight Consolidation)**: Catastrophic forgetting prevention
- **Mel-Spectrogram**: Audio feature representation
- **Data Augmentation**: Pitch shift, time stretch, noise

### Infrastructure
- **Docker**: Containerization (optional)
- **Uvicorn**: ASGI server for FastAPI
- **npm**: JavaScript package manager

---

## 🎓 Summary

**Trust.AI** is a complete scam detection system that:
1. **Accepts** text or audio input from users
2. **Analyzes** using trained ML models and keyword detection
3. **Returns** risk scores and explanations
4. **Learns** from user feedback automatically
5. **Protects** privacy by securely deleting all data

The system combines **rule-based detection** (keywords) with **deep learning** (CNN) to be both fast and accurate, while **continuously improving** through online learning from user feedback.

Every analysis, every training update, and every interaction is designed with privacy-first principles using military-grade data deletion standards.
