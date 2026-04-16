# Online Learning - Quick Start

## What Was Added

Three new files + integration with existing services:

```
backend/
├── app/
│   ├── services/
│   │   └── online_learning.py        ✨ NEW: Core service
│   ├── routes/
│   │   └── feedback.py               ✨ NEW: API endpoints
│   ├── models/
│   │   └── schemas.py                📝 UPDATED: New schemas
│   └── main.py                       📝 UPDATED: Initialize service
└── ONLINE_LEARNING_GUIDE.md         ✨ NEW: Full documentation
```

## Usage Flow

```
1. User gets analysis result
   ├─ Risk Score: 75/100
   ├─ Model Confidence: 85%
   ├─ Audio: suspicious_call.wav
   
2. User provides feedback
   └─ POST /api/feedback/audio
      ├─ file: suspicious_call.wav
      ├─ correct_label: 1 (deepfake)
      └─ model_prediction: 0.75
      
3. Backend processes
   ├─ Check if should learn (confidence-based)
   ├─ Extract mel-spectrogram
   ├─ Securely delete audio (3-pass overwrite)
   ├─ Add to training buffer
   ├─ If buffer full (4 samples): Train model
   │  ├─ Apply EWC (prevent forgetting)
   │  ├─ Low learning rate (1e-5)
   │  ├─ Gradient clipping (stability)
   │  └─ Save checkpoint
   └─ Return success
   
4. Response
   └─ {
        "success": true,
        "message": "Model trained on 4 samples",
        "data_deleted": true,
        "model_version": 5
      }
```

## Start Using It

### 1. Backend Auto-Initializes
```bash
cd backend
python -m uvicorn app.main:app --reload

# Logs will show:
# "✓ Online learning service initialized"
```

### 2. Submit Feedback (Python)
```python
import requests

with open('audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/feedback/audio',
        files={'file': f},
        data={
            'correct_label': 1,
            'model_prediction': 0.75
        }
    )
    print(response.json())
```

### 3. Check Status
```bash
curl http://localhost:8000/api/feedback/status
```

### 4. Frontend Integration
```typescript
// Add feedback buttons to your results component
<button onClick={() => submitFeedback(0)}>✓ Correct</button>
<button onClick={() => submitFeedback(1)}>✗ Wrong</button>
```

## Key Features

✅ **Secure Deletion**: Audio deleted with DoD 5220.22-M (3-pass overwrite)  
✅ **No Poisoning**: Skips learning when model is confident & correct  
✅ **No Forgetting**: EWC prevents losing original knowledge  
✅ **Batch Training**: Groups samples for stability  
✅ **Auto Rollback**: Reverts model if training fails  
✅ **Checkpointing**: Keeps history for debugging  

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/feedback/audio` | Submit feedback |
| GET | `/api/feedback/status` | Get training status |
| POST | `/api/feedback/flush` | Force training now |
| GET | `/api/health/learning` | Service health |

## Files Changed

### `backend/app/main.py`
- Import feedback routes
- Initialize online learning on startup
- Register `/api/feedback/*` endpoints

### `backend/app/models/schemas.py`
- Added `FeedbackResponse` schema
- Added `TrainingStatusResponse` schema

### NEW: `backend/app/services/online_learning.py`
- `SecureDeletion`: 3-pass secure deletion
- `ElasticWeightConsolidation`: Prevent forgetting
- `OnlineLearningService`: Main service

### NEW: `backend/app/routes/feedback.py`
- `POST /api/feedback/audio`: Submit feedback
- `GET /api/feedback/status`: Check status
- `POST /api/feedback/flush`: Flush buffer
- `GET /api/health/learning`: Health check

## Configuration

Default settings in `backend/app/routes/feedback.py`:

```python
OnlineLearningConfig(
    learning_rate=1e-5,         # Very low (prevent forgetting)
    batch_size=4,               # Train in groups of 4
    confidence_threshold=0.70,  # Skip if >70% confident & correct
    ewc_lambda=0.1,            # EWC strength
    gradient_clip=0.01,         # Stability
)
```

Change these to tune behavior:
- **More aggressive**: Lower learning rate, higher batch size
- **More conservative**: Higher learning rate, lower batch size

## Example Response

```json
{
  "success": true,
  "message": "Model trained on 4 feedback samples",
  "data_deleted": true,
  "model_trained": true,
  "training_loss": 0.3421,
  "buffer_size": 0,
  "model_version": 5
}
```

Fields:
- `data_deleted`: Audio was securely deleted
- `model_trained`: Model was updated (false if skipped due to confidence)
- `model_version`: Current model version number
- `buffer_size`: Samples waiting for training
- `training_loss`: Loss on the batch (lower is better)

## Monitoring

```bash
# Watch online learning in real-time
tail -f backend.log | grep "online_learning\|Model trained\|feedback"

# Check status endpoint
curl http://localhost:8000/api/feedback/status | jq .
```

Expected output:
```json
{
  "operational": true,
  "model_version": 5,
  "feedback_buffer_size": 0,
  "checkpoints_saved": 5,
  "learning_rate": 1e-5,
  "batch_size": 4,
  "ewc_enabled": true
}
```

## Important Notes

1. **Audio is deleted**: File is permanently overwritten 3 times and deleted
2. **No persistent storage**: Only model weights are saved, never audio
3. **Privacy-first**: Fulfills "no data persistence" requirement
4. **Improves over time**: Model gets better as more feedback comes in
5. **Backward compatible**: Existing API unchanged, only extended

## Troubleshooting

### "Service not operational"
```bash
# Check logs
python -m uvicorn app.main:app --reload 2>&1 | grep online_learning

# Verify imports work
python -c "from app.services.online_learning import OnlineLearningService; print('✓')"
```

### Data not deleted
- Check file permissions (must have write access)
- Verify temp directory space
- Check logs for deletion errors

### Model not improving
- Check `model_version` increases
- May need more feedback samples
- Try lowering `confidence_threshold` to learn more

## Next Steps

1. Add feedback UI buttons to frontend
2. Monitor `/api/feedback/status` endpoint
3. Track model improvement metrics
4. Adjust config based on feedback patterns
5. Deploy to production with confidence

---

**Ready to use!** Model will improve automatically as users provide feedback. 🚀
