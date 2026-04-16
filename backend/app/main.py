"""
TRUST.AI Backend - FastAPI Server for Scam Detection
Main application entry point

Features:
- Text scam detection
- Audio deepfake detection with CNN
- Online learning with user feedback
- Privacy-first (no data persistence)
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging

# Import routes
from app.routes import analyze_text, analyze_audio, feedback

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: Import CNN model (requires torch)
try:
    from app.services.cnn_deepfake_detector import CNNDeepfakeDetector
    from app.models.cnn_model import DeepfakeCNN
    CNN_AVAILABLE = True
    logger.info("✓ CNN/torch dependencies available")
except ImportError as e:
    logger.warning(f"torch/CNN not available - deepfake detection will use heuristic only: {e}")
    CNN_AVAILABLE = False

# Create FastAPI app
app = FastAPI(
    title="TRUST.AI API",
    description="AI-powered scam detection for text and voice with online learning",
    version="1.0.0"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "service": "trust-ai-backend"}

# Initialize online learning service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize online learning service with CNN model (if available)."""
    logger.info("=" * 60)
    logger.info("BACKEND STARTUP")
    logger.info("=" * 60)
    
    if not CNN_AVAILABLE:
        logger.warning("CNN not available - text analysis only will be functional")
        logger.info("=" * 60)
        return
    
    try:
        model_path = Path(__file__).parent.parent / 'models' / 'cnn_deepfake_best.pt'
        
        logger.info(f"Loading trained CNN model from: {model_path}")
        logger.info(f"Model file exists: {model_path.exists()}")
        
        # Create CNN model
        model = DeepfakeCNN()
        logger.info("✓ CNN model architecture created")
        
        # Initialize online learning
        feedback.init_online_learning(
            model=model,
            model_path=str(model_path)
        )
        
        logger.info("✓ Online learning service initialized")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to initialize online learning: {e}", exc_info=True)
        logger.info("=" * 60)

# Include routes
app.include_router(analyze_text.router, prefix="/api", tags=["text"])
app.include_router(analyze_audio.router, prefix="/api", tags=["audio"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
