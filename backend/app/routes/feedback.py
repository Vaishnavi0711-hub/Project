"""
Feedback routes for online learning
Allows users to report if analysis was correct/incorrect to improve the model.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
import logging
import tempfile
import os
from typing import Optional

from app.models.schemas import FeedbackResponse, TrainingStatusResponse
from app.services.cnn_deepfake_detector import CNNDeepfakeDetector

logger = logging.getLogger(__name__)
router = APIRouter()

# Global online learning service (initialized when module is loaded)
online_learning_service: Optional[object] = None

# Check if torch is available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def init_online_learning(model, model_path: str = 'models/cnn_deepfake_best.pt'):
    """Initialize online learning service. Call from main.py"""
    global online_learning_service
    
    if not TORCH_AVAILABLE:
        logger.warning("Torch not available - online learning disabled")
        return
    
    try:
        # Import dynamically when torch is available
        from app.services.online_learning import OnlineLearningService, OnlineLearningConfig
        
        config = OnlineLearningConfig(
            learning_rate=1e-5,
            gradient_clip=0.01,
            batch_size=4,
            ewc_lambda=0.1
        )
        
        online_learning_service = OnlineLearningService(
            model=model,
            model_path=model_path,
            config=config
        )
        logger.info("Online learning service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize online learning: {e}")
        online_learning_service = None


@router.post(
    "/feedback/audio",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit audio feedback to improve model",
    description="User provides an audio file with the correct label to help train the model. "
                "Audio is securely deleted after training."
)
async def submit_audio_feedback(
    file: UploadFile = File(...),
    correct_label: int = Query(..., ge=0, le=1, description="0=real speech, 1=deepfake"),
    model_prediction: Optional[float] = Query(None, ge=0, le=1, description="Original model prediction"),
):
    """
    Submit feedback to improve the model.
    
    The audio file is immediately processed and securely deleted.
    Data is never stored long-term.
    
    Args:
        file: Audio file (wav, mp3, etc.)
        correct_label: Correct label (0=real, 1=deepfake)
        model_prediction: Optional - the model's original prediction for reference
        
    Returns:
        FeedbackResponse with status and training information
    """
    
    if online_learning_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Online learning service is not available"
        )
    
    if correct_label not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="correct_label must be 0 (real) or 1 (deepfake)"
        )
    
    temp_file = None
    try:
        logger.info(f"Feedback received: {file.filename}, label={correct_label}")
        
        # Save to temporary file
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(content)
            temp_file = tmp.name
        
        # Get model prediction label
        model_prediction_label = 1 if (model_prediction and model_prediction > 0.5) else 0
        model_pred_prob = model_prediction or 0.5
        
        # Process feedback (includes feature extraction and secure deletion)
        result = await online_learning_service.learn_from_feedback(
            audio_path=temp_file,
            user_label=correct_label,
            model_prediction=model_pred_prob,
            model_prediction_label=model_prediction_label,
            delete_audio=True,
            async_training=False  # Train immediately for guaranteed consistency
        )
        
        logger.info(
            f"Feedback processed: {result.get('message', 'success')} "
            f"(data_deleted={result.get('data_deleted', False)})"
        )
        
        return FeedbackResponse(
            success=result.get('success', False),
            message=result.get('message', 'Feedback submitted'),
            data_deleted=result.get('data_deleted', False),
            model_trained=not result.get('skipped', False),
            training_loss=result.get('training_loss'),
            buffer_size=result.get('buffer_size', 0),
            model_version=result.get('model_version', 0),
            skipped_reason=result.get('reason')
        )
        
    except Exception as e:
        logger.error(f"Feedback processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}"
        )
    
    finally:
        # Emergency cleanup (online learning should have handled it)
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.warning("Emergency cleanup: removed temp file")
            except Exception as e:
                logger.error(f"Emergency cleanup failed: {e}")


@router.get(
    "/feedback/status",
    response_model=TrainingStatusResponse,
    summary="Get online learning status",
    description="Get current training buffer size and model version"
)
async def get_training_status():
    """
    Get status of online learning service.
    
    Returns:
        Current buffer size, model version, and configuration
    """
    
    if online_learning_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Online learning service is not available"
        )
    
    status_info = online_learning_service.get_training_status()
    
    return TrainingStatusResponse(
        operational=True,
        model_version=status_info['model_version'],
        feedback_buffer_size=status_info['buffer_size'],
        checkpoints_saved=status_info['checkpoints'],
        learning_rate=status_info['config']['learning_rate'],
        batch_size=status_info['config']['batch_size'],
        ewc_enabled=status_info['config']['ewc_lambda'] > 0
    )


@router.post(
    "/feedback/flush",
    summary="Train on remaining feedback immediately",
    description="Force training on any pending feedback samples"
)
async def flush_feedback_buffer():
    """
    Immediately train on all feedback in the buffer.
    Useful before shutdown or deployment.
    
    Returns:
        Training results
    """
    
    if online_learning_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Online learning service is not available"
        )
    
    result = await online_learning_service.flush_buffer()
    
    return {
        'success': result.get('success', False),
        'message': result.get('message', 'Flushed'),
        'trained_samples': result.get('batch_size', 0),
        'model_version': result.get('model_version', 0)
    }


@router.get(
    "/health/learning",
    summary="Health check for online learning",
    description="Verify online learning service is operational"
)
async def health_check_learning():
    """Health check endpoint for online learning service."""
    
    operational = online_learning_service is not None
    
    return {
        'service': 'online_learning',
        'operational': operational,
        'status': 'ready' if operational else 'unavailable'
    }
