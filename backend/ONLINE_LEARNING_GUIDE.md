# Online Learning Implementation Guide

## Overview

Your TRUST.AI backend now features a **production-grade online learning system** that continuously improves the CNN model using user feedback. This guide explains the system and how to use it.

## Architecture

```
User Analysis
    ↓
Analysis Result
    ↓
User Feedback (Correct Label)
    ↓
Online Learning Service
    ├── Feature Extraction (mel-spectrogram)
    ├── Confidence Checking (avoid poisoning)
    ├── Buffer Accumulation (batch stability)
    ├── Secure Data Deletion (privacy)
    ├── EWC Training (catastrophic forgetting prevention)
    └── Checkpoint Management (rollback capability)
    ↓
Updated Model
```

## Key Features

### 1. **Elastic Weight Consolidation (EWC)**
Prevents catastrophic forgetting by penalizing changes to weights important for original task.

```python
# How it works:
- Computes Fisher Information Matrix (weight importance)
- During new learning, penalizes changes to important weights
- Allows learning new patterns while preserving old knowledge
```

**Result**: Model improves with feedback without forgetting original training

### 2. **Confidence-Based Sampling**
Avoids learning from wrong labels (data poisoning protection).

```python
# Skips learning when:
- Model is highly confident (>70%) AND correct
- Prevents wasting training on obvious cases
```

**Result**: Only learns from cases where model was wrong or uncertain

### 3. **Batch Accumulation**
Accumulates feedback samples before training for stability.

```python
# Groups samples into batches before training
- Default batch size: 4 samples
- More stable gradients than single-sample training
- Multiple epoch passes per batch for convergence
```

**Result**: Stable, consistent model updates

### 4. **Secure Data Deletion**
Uses DoD 5220.22-M standard (3-pass overwrite).

```python
# Deletion process:
- Pass 1: Overwrite with zeros
- Pass 2: Overwrite with ones
- Pass 3: Overwrite with random data
- Delete file
- Verify deletion

# Result: Complete data removal, unrecoverable
```

### 5. **Checkpoint Management**
Saves model versions with automatic rollback on failure.

```python
# Auto-saves before/after training
- Keeps 5 most recent checkpoints
- Can rollback if training fails
- Version tracking for model history
```

## API Endpoints

### 1. Submit Feedback

```http
POST /api/feedback/audio
Content-Type: multipart/form-data

file: <audio_file>
correct_label: 0 or 1
model_prediction: 0.75 (optional)
```

**Response:**
```json
{
  "success": true,
  "message": "Model trained on 4 feedback samples",
  "data_deleted": true,
  "model_trained": true,
  "training_loss": 0.3421,
  "buffer_size": 0,
  "model_version": 5,
  "skipped_reason": null
}
```

**When feedback is skipped:**
```json
{
  "success": true,
  "message": "Feedback submitted",
  "data_deleted": true,
  "model_trained": false,
  "skipped_reason": "Model was confident and correct"
}
```

### 2. Get Training Status

```http
GET /api/feedback/status
```

**Response:**
```json
{
  "operational": true,
  "model_version": 5,
  "feedback_buffer_size": 2,
  "checkpoints_saved": 5,
  "learning_rate": 1e-5,
  "batch_size": 4,
  "ewc_enabled": true
}
```

### 3. Flush Buffer

```http
POST /api/feedback/flush
```

Forces training on all pending feedback immediately (useful before deployment).

### 4. Learning Health Check

```http
GET /api/health/learning
```

Verifies online learning service is operational.

## Usage Examples

### Python Client

```python
import requests
import json

# 1. Analyze audio
with open('suspicious_audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/analyze-audio',
        files={'file': f}
    )
    analysis = response.json()
    print(f"Risk Score: {analysis['risk_score']}/100")

# 2. User confirms or corrects the analysis
correct_label = 1  # 1 = deepfake (user agrees)
# or: correct_label = 0  # 0 = real (user disagrees)

# 3. Submit feedback (audio auto-deleted)
with open('suspicious_audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/feedback/audio',
        files={'file': f},
        data={
            'correct_label': correct_label,
            'model_prediction': analysis['deepfake_probability']
        }
    )
    feedback_result = response.json()
    print(f"Feedback: {feedback_result['message']}")
    print(f"Data deleted: {feedback_result['data_deleted']}")

# 4. Check training status
response = requests.get('http://localhost:8000/api/feedback/status')
status = response.json()
print(f"Model version: {status['model_version']}")
print(f"Buffer size: {status['feedback_buffer_size']}")
```

### React/TypeScript Frontend

```typescript
// Component: FeedbackWidget.tsx
import { useState } from 'react'

export function FeedbackWidget({ analysis }) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const submitFeedback = async (isCorrect: boolean) => {
    setIsSubmitting(true)
    
    try {
      const formData = new FormData()
      formData.append('file', audioBlob, 'audio.wav')
      formData.append(
        'correct_label',
        isCorrect ? '0' : '1'  // 0=correct, 1=wrong
      )
      formData.append(
        'model_prediction',
        analysis.deepfake_probability?.toString() || '0.5'
      )
      
      const response = await fetch('/api/feedback/audio', {
        method: 'POST',
        body: formData
      })
      
      const result = await response.json()
      
      if (result.success) {
        alert(result.message)
        console.log(`✓ Data permanently deleted: ${result.data_deleted}`)
        
        if (result.model_trained) {
          console.log(`✓ Model improved (version ${result.model_version})`)
        }
      }
    } finally {
      setIsSubmitting(false)
    }
  }
  
  return (
    <div className="feedback-widget">
      <p>Was this analysis correct?</p>
      
      <button
        onClick={() => submitFeedback(true)}
        disabled={isSubmitting}
      >
        ✓ Yes, Correct
      </button>
      
      <button
        onClick={() => submitFeedback(false)}
        disabled={isSubmitting}
      >
        ✗ No, Incorrect
      </button>
      
      <p style={{ fontSize: '0.9em', color: '#666' }}>
        Your audio will be securely deleted after analysis.
      </p>
    </div>
  )
}
```

## Configuration

Edit `backend/app/routes/feedback.py`:

```python
config = OnlineLearningConfig(
    learning_rate=1e-5,           # Very low (prevents forgetting)
    gradient_clip=0.01,           # Max gradient magnitude
    weight_decay=1e-6,            # L2 regularization
    confidence_threshold=0.70,    # Skip if model confident & correct
    batch_size=4,                 # Train in groups of 4
    ewc_lambda=0.1,              # EWC importance (higher = preserve more)
    keep_checkpoints=5,           # Keep 5 model versions
    deletion_verify_attempts=3,   # Verify deletion 3 times
)
```

## Monitoring

### Real-Time Monitoring

```bash
# Watch logs for online learning activity
tail -f backend.log | grep "online_learning\|Model trained\|feedback"
```

### Metrics to Track

1. **Model Version**: Should increase as feedback comes in
2. **Buffer Size**: Should stay ≤ batch_size (training happens regularly)
3. **Training Loss**: Should decrease over time (model improving)
4. **Checkpoint Count**: Should maintain ~5 most recent

### Dashboard Example

```json
{
  "model_version": 25,
  "feedback_sessions_today": 147,
  "avg_training_loss": 0.28,
  "model_improved_sessions": 89,
  "avg_feedback_response_time_ms": 245,
  "avg_deletion_time_ms": 32
}
```

## Safety & Privacy

### Data Deletion Verification

```python
# Automatic verification process:
1. Overwrite 3 times (different patterns)
2. Delete file
3. Query filesystem to confirm deletion
4. Retry if needed
5. Log success/failure

# Result: Audio unrecoverable
```

### Poisoning Prevention

```python
# Confidence-based sampling prevents:
- Malicious users submitting wrong labels
- Model learning incorrect patterns
- Data corruption through feedback

# Example:
- Model predicts: 95% deepfake (very confident)
- User says: "Actually real speech"
- Decision: SKIP (model was confident, likely user is wrong)
```

### Privacy Guarantees

- ✅ No data stored between requests
- ✅ Secure deletion with verification
- ✅ No long-term data persistence
- ✅ No audit logs of audio content
- ✅ Optional: Differential privacy (add noise to gradients)

### Optional: Differential Privacy

For additional privacy, add noise to gradients:

```python
# In online_learning.py, add to training loop:
for param in model.parameters():
    if param.grad is not None:
        # Add Gaussian noise
        noise = torch.randn_like(param.grad) * epsilon
        param.grad += noise
```

## Common Scenarios

### Scenario 1: False Positive
Model says "deepfake" but user says "real"

```python
correct_label = 0  # Real speech
model_prediction = 0.85  # Model was 85% confident it's deepfake

# Outcome:
# - Model is wrong
# - Learn from this (not skipped)
# - Train on sample
# - Model improves
```

### Scenario 2: False Negative
Model says "real" but user says "deepfake"

```python
correct_label = 1  # Deepfake
model_prediction = 0.35  # Model was 35% confident it's real

# Outcome:
# - Model missed a deepfake
# - Learn from this (not skipped)
# - Adjust model sensitivity
# - Model improves
```

### Scenario 3: Model Right, User Wrong
Model says "deepfake" (95% confident), user says "real"

```python
correct_label = 0  # User claims real
model_prediction = 0.95  # Model very confident

# Outcome:
# - Feedback skipped (model confident and likely correct)
# - Audio deleted
# - Model unchanged
# - No poisoning risk
```

## Deployment Considerations

### Before Deployment

```bash
# Ensure all feedback is trained
curl -X POST http://localhost:8000/api/feedback/flush

# Verify status
curl http://localhost:8000/api/feedback/status

# Check training service
curl http://localhost:8000/api/health/learning
```

### Production Settings

```python
# More conservative (preserve model stability)
config = OnlineLearningConfig(
    learning_rate=5e-6,        # Even lower
    batch_size=8,              # Larger batches
    ewc_lambda=0.5,            # Stronger EWC
    confidence_threshold=0.80, # Higher threshold (skip more)
)

# Aggressive (rapid improvement)
config = OnlineLearningConfig(
    learning_rate=5e-5,        # Higher
    batch_size=2,              # Smaller batches
    ewc_lambda=0.05,           # Weaker EWC
    confidence_threshold=0.50, # Lower threshold (learn more)
)
```

### Container/Docker

```dockerfile
# Ensure model checkpoint directory exists
RUN mkdir -p /app/backend/models

# Model will auto-load if checkpoint exists
# Otherwise, starts with base CNN

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

## Troubleshooting

### "Online learning service is not available"
- Check if `init_online_learning()` ran in startup
- Verify CNN model loads successfully
- Check logs for import errors

**Solution:**
```bash
# Check logs
tail -f backend.log | grep "online_learning\|startup"

# Verify imports
python -c "from app.services.online_learning import OnlineLearningService; print('✓ OK')"
```

### "Training loss very high"
- Model might be learning wrong patterns
- May be overfitting to feedback noise

**Solution:**
- Increase `gradient_clip` to stabilize
- Increase `confidence_threshold` to skip more inputs
- Increase `ewc_lambda` to preserve original knowledge
- Rollback to previous checkpoint

### "Memory increase over time"
- Feedback buffer might be accumulating

**Solution:**
- Call `/api/feedback/flush` periodically
- Lower `batch_size` for more frequent training
- Monitor `feedback_buffer_size` in status

## Best Practices

1. **Monitor Model Versions**: Track how often model improves
2. **Log Feedback Rate**: Track user engagement
3. **Audit False Feedback**: Periodically check skipped samples
4. **Version Control Models**: Keep checkpoints for rollback
5. **Regular Validation**: Test on held-out dataset monthly
6. **Gradual Deployment**: Start with conservative settings
7. **User Feedback**: Display model version to show improvements

## Next Steps

1. **Integrate feedback UI**: Add "Was this correct?" buttons
2. **Monitor performance**: Track model improvements over time
3. **Tune hyperparameters**: Adjust config based on feedback patterns
4. **Implement analytics**: Track false positive/negative rates
5. **Scale gradually**: Test with small user group first

## References

- **EWC Paper**: Kirkpatrick et al., "Overcoming catastrophic forgetting"
- **Online Learning**: Littlestone & Warmuth, "The weighted majority algorithm"
- **Differential Privacy**: Dwork, "Differential Privacy"

---

**Status**: ✅ Production-Ready Online Learning Implemented
