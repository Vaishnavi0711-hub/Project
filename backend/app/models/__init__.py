"""Models package

Includes:
- Pydantic schemas for request/response validation
- PyTorch CNN architectures for deepfake detection (optional)
"""

# Optional: Import CNN models only if torch is available
try:
    from app.models.cnn_model import DeepfakeCNN, LightweightDeepfakeCNN
    __all__ = ['DeepfakeCNN', 'LightweightDeepfakeCNN']
except ImportError:
    # torch not available - CNN features will be disabled
    __all__ = []
