"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Click here immediately to verify your PayPal account or it will be suspended!"
            }
        }

class AudioAnalysisRequest(BaseModel):
    """Request for audio analysis"""
    pass  # File is handled separately in multipart form

class RiskAssessment(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0-100")
    threat_types: List[str] = Field(default_factory=list, description="Types of threats detected")
    explanation: str = Field(..., description="Explanation of the assessment")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level of the assessment")

class TextAnalysisResponse(RiskAssessment):
    """Response for text analysis"""
    class Config:
        json_schema_extra = {
            "example": {
                "risk_score": 85,
                "threat_types": ["phishing_attempt", "identity_theft_attempt"],
                "explanation": "This message contains phishing indicators and attempts to create urgency around account verification.",
                "confidence": 0.92
            }
        }

class AudioAnalysisResponse(RiskAssessment):
    """Response for audio analysis"""
    transcription: str = Field(..., description="Transcription of the audio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "risk_score": 90,
                "threat_types": ["identity_theft", "impersonation"],
                "explanation": "This call attempts to impersonate a bank and requests sensitive information.",
                "confidence": 0.88,
                "transcription": "This is your bank calling about unauthorized transactions..."
            }
        }

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid file type. Please upload an audio file."
            }
        }


class FeedbackResponse(BaseModel):
    """Response for feedback submission"""
    success: bool = Field(..., description="Whether feedback was processed successfully")
    message: str = Field(..., description="Status message")
    data_deleted: bool = Field(..., description="Whether audio file was securely deleted")
    model_trained: bool = Field(default=True, description="Whether model was trained on this feedback")
    training_loss: Optional[float] = Field(None, description="Training loss if model was trained")
    buffer_size: int = Field(default=0, description="Current feedback buffer size")
    model_version: int = Field(default=0, description="Current model version")
    skipped_reason: Optional[str] = Field(None, description="Reason if feedback was skipped")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Model trained on 4 feedback samples",
                "data_deleted": True,
                "model_trained": True,
                "training_loss": 0.3421,
                "buffer_size": 0,
                "model_version": 5,
                "skipped_reason": None
            }
        }


class TrainingStatusResponse(BaseModel):
    """Response for training status query"""
    operational: bool = Field(..., description="Is online learning service operational")
    model_version: int = Field(..., description="Current trained model version")
    feedback_buffer_size: int = Field(..., description="Number of pending feedback samples")
    checkpoints_saved: int = Field(..., description="Number of model checkpoints saved")
    learning_rate: float = Field(..., description="Current learning rate")
    batch_size: int = Field(..., description="Feedback batch size")
    ewc_enabled: bool = Field(..., description="Is Elastic Weight Consolidation enabled")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operational": True,
                "model_version": 5,
                "feedback_buffer_size": 2,
                "checkpoints_saved": 5,
                "learning_rate": 1e-5,
                "batch_size": 4,
                "ewc_enabled": True
            }
        }
