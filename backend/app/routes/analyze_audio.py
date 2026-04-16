"""
Audio scam detection route

Features:
- Speech-to-text transcription (Whisper)
- Text-based scam detection (keyword analysis)
- Audio deepfake detection (CNN or heuristic)
- Combined risk assessment
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
import logging
import tempfile
import os
from pathlib import Path

logger  = logging.getLogger(__name__)

from app.models.schemas import AudioAnalysisResponse
from app.services.speech_to_text import SpeechToTextService
from app.services.deepfake_detector import DeepfakeDetector
from app.services.text_detector import TextScamDetector

# Optional: CNN deepfake detector (requires torch)
try:
    from app.services.cnn_deepfake_detector import CNNDeepfakeDetector
    CNN_AVAILABLE = True
except (ImportError, NameError):
    CNN_AVAILABLE = False
    logger.warning("CNN deepfake detector not available - will use heuristic fallback")
router = APIRouter()

# Initialize services
speech_service = SpeechToTextService()
heuristic_detector = DeepfakeDetector()
text_detector = TextScamDetector()

# Initialize CNN detector (with fallback to heuristic)
cnn_detector = None
if CNN_AVAILABLE:
    model_path = Path(__file__).parent.parent.parent / 'models' / 'cnn_deepfake_best.pt'
    try:
        cnn_detector = CNNDeepfakeDetector(
            model_path=str(model_path) if model_path.exists() else None,
            device='cpu'
        )
        logger.info("CNN deepfake detector initialized")
    except Exception as e:
        logger.warning(f"CNN detector initialization failed, using heuristics only: {e}")
        cnn_detector = None
else:
    logger.info("Using heuristic-only deepfake detection (torch not installed)")

@router.post(
    "/analyze-audio",
    response_model=AudioAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze audio for scam indicators",
    description="Analyzes provided audio file for voice spoofing, deepfakes, and fraudulent content"
)
async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze audio file for scam indicators.
    
    Process:
    1. Convert audio to text using Whisper
    2. Analyze text for scam indicators
    3. Analyze audio features for deepfake/spoofing
    
    Returns:
    - risk_score: Combined score from text and audio analysis
    - threat_types: List of detected threat categories
    - explanation: Human-readable explanation
    - confidence: Model confidence (0-1)
    - transcription: Transcribed text from audio
    """
    
    # Validate file
    allowed_types = {"audio/mpeg", "audio/wav", "audio/webm", "audio/ogg", "audio/mp4"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Check file size (25MB limit)
    max_size = 25 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 25MB limit"
        )
    
    temp_file = None
    try:
        logger.info(f"Processing audio file: {file.filename}")
        logger.info(f"File size: {len(content)} bytes")
        logger.info(f"Content type: {file.content_type}")
        
        # Save to temporary file with proper format detection
        suffix = Path(file.filename).suffix if file.filename else ""
        if not suffix or suffix.lower() not in ['.wav', '.mp3', '.flac', '.ogg', '.webm']:
            suffix = ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp.flush()  # Ensure data is written to disk
            temp_file = tmp.name
        
        # Convert to absolute path for consistency across platforms
        temp_file_path = Path(temp_file).resolve()
        temp_file_str = str(temp_file_path)
        
        logger.info(f"Temporary file created: {temp_file_str}")
        logger.info(f"Temp file size: {temp_file_path.stat().st_size} bytes")
        logger.info(f"Temp file exists: {temp_file_path.exists()}")
        logger.info(f"Temp file is_file: {temp_file_path.is_file()}")
        
        # Speech-to-text
        logger.info("Transcribing audio...")
        transcription = await speech_service.transcribe(temp_file_str)
        logger.info(f"Transcription result: {transcription[:100]}...")
        
        # Analyze transcription for text-based scams
        logger.info("Analyzing transcription for scam indicators...")
        text_analysis = text_detector.analyze(transcription)
        
        # Analyze audio features for deepfake/spoofing
        logger.info("Analyzing audio features for deepfake/spoofing...")
        if cnn_detector is not None:
            # Use CNN detector (with fallback to heuristic)
            audio_features = await cnn_detector.analyze(temp_file_str)
            logger.info(f"CNN model used: {audio_features.get('model_loaded', False)}")
        else:
            # Fall back to heuristic detector
            audio_features = await heuristic_detector.analyze(temp_file_str)
            logger.info("Heuristic detector used (CNN unavailable)")
        
        
        # SMART COMBINATION OF ANALYSES
        # If either analysis detects high risk, overall should be high
        text_risk = text_analysis['risk_score']
        audio_risk = audio_features['risk_score']
        
        # Use max when both agree (conservative scoring)
        # If one is high and one is uncertain, take the higher
        if text_risk > 60 or audio_risk > 60:
            # One signals danger - that's our answer
            combined_risk = int(max(text_risk, audio_risk))
        elif text_risk > 40 or audio_risk > 40:
            # One signals medium concern - boost it
            combined_risk = int(max(text_risk, audio_risk) * 0.9)
        else:
            # Both low - use weighted average (60% text, 40% audio for voice content)
            combined_risk = int(text_risk * 0.6 + audio_risk * 0.4)
        
        combined_risk = min(100, max(0, combined_risk))
        
        # Merge threat types and add meta-threats
        all_threats = list(set(text_analysis['threat_types'] + audio_features['threat_types']))
        
        # Add uncertainty warning if either analysis is uncertain
        if text_analysis.get('confidence', 1.0) < 0.65 or audio_features.get('confidence', 1.0) < 0.65:
            if 'analysis_uncertainty' not in all_threats:
                all_threats.append('analysis_uncertainty')
        
        # Create combined explanation
        explanation = f"Text analysis: {text_analysis['explanation']} | "
        explanation += f"Audio analysis: {audio_features['explanation']}"
        
        # Combined confidence (lower if either is uncertain)
        combined_confidence = (text_analysis['confidence'] + audio_features['confidence']) / 2
        combined_confidence = min(combined_confidence, min(text_analysis['confidence'], audio_features['confidence']) + 0.1)
        
        logger.info(f"Audio analysis complete. Risk score: {combined_risk}")
        
        return AudioAnalysisResponse(
            risk_score=combined_risk,
            threat_types=all_threats,
            explanation=explanation.strip(),
            confidence=combined_confidence,
            transcription=transcription
        )
        
    except Exception as e:
        logger.error(f"Error analyzing audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze audio"
        )
    
    finally:
        # Cleanup temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
                logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up temp file: {e}")
