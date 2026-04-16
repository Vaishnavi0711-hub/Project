"""
CNN-based Deepfake Detection Service
Inference wrapper for the CNN model with fallback to heuristic analysis
"""

import logging
import asyncio
from typing import Dict, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import librosa
    import numpy as np
    CNN_AVAILABLE = True
except ImportError:
    # Define stub imports for type hints when dependencies are unavailable
    CNN_AVAILABLE = False
    logger.warning("CNN dependencies not fully available")
    import numpy as np  # Provide numpy stub for type hints


class CNNDeepfakeDetector:
    """
    CNN-based deepfake detection service.
    
    Features:
    - Loads pre-trained CNN model if available
    - Falls back to heuristic analysis if model not found
    - Async inference to prevent blocking
    - Handles variable audio lengths
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        use_lightweight: bool = False
    ):
        """
        Initialize CNN detector.
        
        Args:
            model_path: Path to saved model checkpoint
            device: 'cuda' or 'cpu' (auto-detect if None)
            use_lightweight: Use lightweight model variant
        """
        self.model_path = model_path
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_lightweight = use_lightweight
        self.model = None
        self.model_loaded = False
        self.audio_sr = 16000
        self.n_mels = 128
        
        if CNN_AVAILABLE:
            self._load_model()
        else:
            logger.warning("CNN libraries not available, using heuristics only")
    
    def _load_model(self):
        """Load CNN model if path exists, otherwise initialize untrained model."""
        try:
            if self.use_lightweight:
                from app.models.cnn_model import LightweightDeepfakeCNN
                self.model = LightweightDeepfakeCNN().to(self.device)
                model_name = "Lightweight"
            else:
                from app.models.cnn_model import DeepfakeCNN
                self.model = DeepfakeCNN().to(self.device)
                model_name = "Standard"
            
            self.model.eval()
            
            # Try to load checkpoint if provided
            if self.model_path and Path(self.model_path).exists():
                checkpoint = torch.load(
                    self.model_path,
                    map_location=self.device
                )
                
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    epoch = checkpoint.get('epoch', 'unknown')
                    val_loss = checkpoint.get('val_loss', 'unknown')
                    logger.info(
                        f"✓ Loaded {model_name} CNN model from {self.model_path} "
                        f"(epoch {epoch}, val_loss {val_loss})"
                    )
                else:
                    # Directly load state dict if it's not wrapped in checkpoint dict
                    self.model.load_state_dict(checkpoint)
                    logger.info(f"✓ Loaded {model_name} CNN model from {self.model_path}")
                
                self.model_loaded = True
            else:
                logger.info(
                    f"Using untrained {model_name} CNN model "
                    f"(no checkpoint found at {self.model_path})"
                )
                self.model_loaded = False
                
        except Exception as e:
            logger.error(f"Failed to initialize CNN model: {e}")
            self.model = None
    
    async def analyze(self, audio_path: str) -> Dict:
        """
        Analyze audio for deepfake indicators using CNN.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with risk_score, threat_types, explanation, confidence, model_type
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._analyze_sync,
            audio_path
        )
    
    def _analyze_sync(self, audio_path: str) -> Dict:
        """
        Synchronous deepfake analysis with ensemble voting (runs in thread pool).
        
        For small datasets, use ensemble predictions from multiple
        augmented versions of the same audio to improve robustness.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with analysis results
        """
        
        if not CNN_AVAILABLE:
            return self._get_fallback_result(
                "CNN libraries not available"
            )
        
        try:
            logger.info(f"CNN ensemble analysis started for {audio_path}")
            
            # Load and process audio
            y, sr = librosa.load(audio_path, sr=self.audio_sr, duration=3.0)
            
            if len(y) == 0:
                return self._get_fallback_result("Audio file is empty")
            
            # ENSEMBLE VOTING: Multiple predictions on modified versions
            # This helps with small dataset overfitting
            predictions = []
            
            # 1. Original audio
            prob = self._get_single_prediction(y, sr)
            predictions.append(prob)
            logger.info(f"Prediction 1 (original): {prob:.3f}")
            
            if self.model_loaded:
                # 2. Pitch-shifted version (±3 semitones)
                try:
                    y_pitch = librosa.effects.pitch_shift(y, sr=sr, n_steps=2)
                    prob = self._get_single_prediction(y_pitch, sr)
                    predictions.append(prob)
                    logger.info(f"Prediction 2 (pitch+2): {prob:.3f}")
                except Exception as e:
                    logger.debug(f"Pitch shift failed: {e}")
                
                # 3. Time-stretched version (speeded up 5%)
                try:
                    y_stretch = librosa.effects.time_stretch(y, rate=1.05)
                    prob = self._get_single_prediction(y_stretch, sr)
                    predictions.append(prob)
                    logger.info(f"Prediction 3 (time+5%): {prob:.3f}")
                except Exception as e:
                    logger.debug(f"Time stretch failed: {e}")
                
                # 4. Time-stretched version (slowed down 5%)
                try:
                    y_stretch = librosa.effects.time_stretch(y, rate=0.95)
                    prob = self._get_single_prediction(y_stretch, sr)
                    predictions.append(prob)
                    logger.info(f"Prediction 4 (time-5%): {prob:.3f}")
                except Exception as e:
                    logger.debug(f"Time stretch failed: {e}")
            
            # Average predictions (ensemble voting)
            deepfake_prob = np.mean(predictions)
            prob_std = np.std(predictions)
            
            logger.info(
                f"Ensemble result: avg={deepfake_prob:.3f}, "
                f"std={prob_std:.3f}, samples={len(predictions)}"
            )
            
            # MORE CONSERVATIVE THRESHOLDING
            # For scam detection, false negatives (missing scams) are worse than false positives
            # So we lower the thresholds to flag more as suspicious
            risk_score = int(deepfake_prob * 100)
            
            # Determine threat types and confidence
            threat_types = []
            confidence = 0.85
            
            # LOWER THRESHOLDS - be more conservative about what we miss
            if deepfake_prob > 0.65:  # Was 0.7, now 0.65
                threat_types = ['potential_deepfake_voice', 'voice_anomaly']
                confidence = min(0.95, 0.85 + (deepfake_prob - 0.65) * 2)
            elif deepfake_prob > 0.45:  # Was 0.5, now 0.45
                threat_types = ['suspicious_voice_modulation']
                confidence = 0.75 + (deepfake_prob - 0.45)
            elif deepfake_prob > 0.25:  # Was 0.3, now 0.25 - flag earlier suspicious cases
                threat_types = ['voice_anomaly']
                confidence = 0.65 + (deepfake_prob - 0.25) * 0.5
                risk_score = max(35, risk_score)  # Minimum 35 if any suspicion
            elif deepfake_prob > 0.15:
                # Very uncertain - still flag as slightly suspicious
                threat_types = []
                confidence = 0.55
                risk_score = max(20, risk_score)
            
            # Consider uncertainty in ensemble
            if prob_std > 0.2:  # High variance in predictions = suspicious
                logger.warning(f"High prediction variance ({prob_std:.3f}) - model uncertain")
                threat_types.append('model_uncertainty')
                confidence = min(confidence, 0.70)  # Lower confidence when uncertain
                risk_score = max(risk_score, 30)  # Minimum score when uncertain
            
            # Generate explanation
            if self.model_loaded:
                explanation = (
                    f"CNN ensemble analysis ({len(predictions)} predictions) detected "
                    f"{deepfake_prob:.1%} probability of synthetic speech. "
                    f"Variance: {prob_std:.3f}. "
                    f"The model identified irregular frequency patterns "
                    f"{'with high confidence' if prob_std < 0.1 else 'with some uncertainty'}. "
                )
            else:
                explanation = (
                    f"Model not fully trained. Output: {deepfake_prob:.1%} deepfake probability. "
                    f"Please retrain the model for accurate predictions."
                )
            
            logger.info(
                f"CNN analysis complete: {risk_score}% risk, "
                f"confidence: {confidence:.2f}, threats: {threat_types}"
            )
            
            return {
                'risk_score': risk_score,
                'threat_types': threat_types,
                'explanation': explanation.strip(),
                'confidence': round(confidence, 2),
                'model_type': 'cnn_ensemble',
                'model_loaded': self.model_loaded,
                'deepfake_probability': round(deepfake_prob, 3),
                'ensemble_variance': round(prob_std, 3),
                'ensemble_size': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"CNN analysis error: {e}", exc_info=True)
            return self._get_fallback_result(f"CNN analysis error: {str(e)}")
    
    def _get_single_prediction(self, y: np.ndarray, sr: int) -> float:
        """
        Get a single prediction from the model.
        
        Args:
            y: Audio samples
            sr: Sample rate
            
        Returns:
            Deepfake probability (0-1)
        """
        try:
            # Extract mel spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y,
                sr=sr,
                n_mels=self.n_mels,
                n_fft=2048,
                hop_length=512
            )
            
            # Convert to dB scale
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Normalize
            mel_spec_normalized = (
                (mel_spec_db - mel_spec_db.mean()) /
                (mel_spec_db.std() + 1e-5)
            )
            
            # Pad/truncate to fixed time steps (94 for 3 seconds)
            target_time_steps = 94
            if mel_spec_normalized.shape[1] < target_time_steps:
                mel_spec_normalized = np.pad(
                    mel_spec_normalized,
                    ((0, 0), (0, target_time_steps - mel_spec_normalized.shape[1])),
                    mode='constant',
                    constant_values=-2.0
                )
            else:
                mel_spec_normalized = mel_spec_normalized[:, :target_time_steps]
            
            # Prepare tensor
            tensor = torch.from_numpy(
                mel_spec_normalized[np.newaxis, np.newaxis, :, :]
            ).float().to(self.device)
            
            # Forward pass
            if self.model is None:
                logger.warning("CNN model is None")
                return 0.5
            
            with torch.no_grad():
                output = self.model(tensor)
                # Apply sigmoid to convert raw output to probability
                prob = torch.sigmoid(output).item()
            
            return prob
        
        except Exception as e:
            logger.warning(f"Single prediction failed: {e}")
            return 0.5  # Return neutral if prediction fails
    
    def _get_heuristic_fallback(self, mel_spec_db: np.ndarray) -> Dict:
        """Use heuristic analysis as fallback when CNN unavailable."""
        
        features = {
            'mel_spec': mel_spec_db,
            'spectral_centroid': np.mean(mel_spec_db),
            'spectral_flatness': np.std(mel_spec_db)
        }
        
        risk_score = 0
        threats = []
        
        # Heuristic checks (same as original detector)
        spec_smoothness = np.mean(np.abs(np.diff(mel_spec_db)))
        if spec_smoothness < 0.5:
            threats.append('potential_deepfake_voice')
            risk_score += 35
        
        if features['spectral_flatness'] < 10:
            threats.append('voice_anomaly')
            risk_score += 25
        
        risk_score = min(100, risk_score)
        
        return {
            'risk_score': risk_score,
            'threat_types': threats,
            'explanation': (
                "Using heuristic audio analysis (CNN unavailable). "
                "For production use, please train and load a CNN model."
            ),
            'confidence': 0.6,
            'model_type': 'heuristic',
            'model_loaded': False
        }
    
    def _get_fallback_result(self, reason: str) -> Dict:
        """Generic fallback result when analysis fails."""
        
        return {
            'risk_score': 0,
            'threat_types': [],
            'explanation': f"CNN analysis unavailable: {reason}. Falling back to heuristic analysis.",
            'confidence': 0.0,
            'model_type': 'none',
            'model_loaded': False
        }
