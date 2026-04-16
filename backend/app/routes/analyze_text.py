"""
Text scam detection route
"""

from fastapi import APIRouter, HTTPException, status
import logging

from app.models.schemas import TextAnalysisRequest, TextAnalysisResponse
from app.services.text_detector import TextScamDetector

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize detector
detector = TextScamDetector()

@router.post(
    "/analyze-text",
    response_model=TextAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze text for scam indicators",
    description="Analyzes provided text for phishing, fraud, and other scam indicators"
)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text message for scam indicators.
    
    Returns:
    - risk_score: 0-100 indicating scam likelihood
    - threat_types: List of detected threat categories
    - explanation: Human-readable explanation
    - confidence: Model confidence (0-1)
    """
    try:
        logger.info(f"Analyzing text: {len(request.text)} characters")
        
        # Perform analysis
        result = detector.analyze(request.text)
        
        logger.info(f"Analysis complete. Risk score: {result['risk_score']}")
        
        return TextAnalysisResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in text analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze text"
        )
