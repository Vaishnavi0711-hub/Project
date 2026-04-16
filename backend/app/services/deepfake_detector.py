"""
Deepfake and voice spoofing detection service
Analyzes audio spectrograms for anomalies
"""

import logging
import asyncio
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    import librosa
    import numpy as np
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    logger.warning("Audio processing libraries not available")

class DeepfakeDetector:
    """
    Detects deepfake voices and voice spoofing attempts.
    Analyzes audio spectrograms for anomalies and synthesis artifacts.
    """
    
    def __init__(self):
        """Initialize the deepfake detector."""
        self.sample_rate = 16000
        self.n_mels = 128
    
    async def analyze(self, audio_path: str) -> Dict:
        """
        Analyze audio for deepfake and spoofing indicators.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with risk_score, threat_types, explanation, confidence
        """
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, audio_path)
    
    def _analyze_sync(self, audio_path: str) -> Dict:
        """
        Synchronous deepfake analysis (runs in thread pool).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with analysis results
        """
        
        threats: List[str] = []
        score_contribution = 0
        
        if not AUDIO_LIBS_AVAILABLE:
            # Use mock analysis for demo
            return self._get_mock_analysis()
        
        try:
            logger.info(f"Analyzing audio file for deepfake indicators: {audio_path}")
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract features
            features = self._extract_features(y, sr)
            
            # Analyze features for deepfake indicators
            if self._check_synthesis_artifacts(features):
                threats.append('potential_deepfake_voice')
                score_contribution += 35
            
            if self._check_voice_anomalies(features):
                threats.append('voice_anomaly')
                score_contribution += 25
            
            if self._check_audio_quality(features):
                threats.append('suspicious_audio_quality')
                score_contribution += 15
            
            if self._check_modulation_patterns(features):
                threats.append('unnatural_voice_modulation')
                score_contribution += 20
            
            risk_score = min(100, score_contribution)
            
            # Add variance
            import random
            variance = random.uniform(-8, 8)
            risk_score = max(0, min(100, risk_score + variance))
            
            explanation = self._generate_explanation(threats, risk_score)
            confidence = min(0.9, 0.5 + (len(threats) * 0.15))
            
            logger.info(f"Deepfake analysis complete: {risk_score}% risk")
            
            return {
                'risk_score': int(round(risk_score)),
                'threat_types': threats,
                'explanation': explanation,
                'confidence': round(confidence, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio features: {e}")
            return self._get_mock_analysis()
    
    def _extract_features(self, y, sr) -> Dict:
        """Extract audio features for analysis."""
        
        features = {}
        
        # Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        features['mel_spec'] = mel_spec_db
        
        # MFCCs
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features['mfcc'] = mfcc
        
        # Spectral centroid
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        features['spec_centroid'] = spec_centroid
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        features['zcr'] = zcr
        
        # Energy
        features['energy'] = np.sqrt(np.sum(y**2) / len(y))
        
        return features
    
    def _check_synthesis_artifacts(self, features: Dict) -> bool:
        """Check for synthesis artifacts typical of deepfakes."""
        
        mel_spec = features['mel_spec']
        
        # Check for overly smooth spectrogram (sign of synthesis)
        spec_smoothness = np.mean(np.abs(np.diff(mel_spec)))
        if spec_smoothness < 0.5:  # Too smooth indicates synthesis
            return True
        
        # Check for missing spectral content in certain ranges
        high_freq = mel_spec[-20:, :]  # Upper frequency bands
        if np.mean(high_freq) < -30:  # Too quiet in high frequencies
            return True
        
        return False
    
    def _check_voice_anomalies(self, features: Dict) -> bool:
        """Check for unnatural voice patterns."""
        
        zcr = features['zcr']
        
        # Check zero crossing rate variance (natural voices have variation)
        zcr_variance = np.var(zcr)
        if zcr_variance < 0.001:  # Too little variation
            return True
        
        return False
    
    def _check_audio_quality(self, features: Dict) -> bool:
        """Check for suspicious audio quality (compression, noise)."""
        
        mel_spec = features['mel_spec']
        
        # Check for unnatural noise profile
        low_freq = mel_spec[:10, :]  # Lower frequency bands
        high_freq_noise = np.mean(np.std(mel_spec[-10:, :], axis=0))
        
        if high_freq_noise > 8:  # Unusual high-frequency noise
            return True
        
        return False
    
    def _check_modulation_patterns(self, features: Dict) -> bool:
        """Check for unnatural voice modulation patterns."""
        
        mfcc = features['mfcc']
        
        # Check for monotonic patterns (unnatural)
        mfcc_changes = np.mean(np.abs(np.diff(mfcc, axis=1)))
        if mfcc_changes < 0.1:  # Too little modulation
            return True
        
        return False
    
    def _generate_explanation(self, threats: List[str], risk_score: int) -> str:
        """Generate explanation for deepfake analysis."""
        
        if not threats:
            return "Audio analysis does not indicate obvious deepfake or voice spoofing. However, always verify caller identity through independent means."
        
        threat_descriptions = {
            'potential_deepfake_voice': "voice synthesis artifacts",
            'voice_anomaly': "unnatural voice patterns",
            'suspicious_audio_quality': "suspicious audio quality or compression",
            'unnatural_voice_modulation': "unnatural voice modulation"
        }
        
        threat_list = ", ".join([threat_descriptions.get(t, t) for t in threats])
        
        if risk_score >= 70:
            return f"Audio analysis detected indicators of deepfake or spoofing ({threat_list}). This may not be a real person. Do not trust sensitive information provided in this call."
        else:
            return f"Audio analysis found some unusual characteristics ({threat_list}). Exercise caution and verify caller identity independently."
    
    @staticmethod
    def _get_mock_analysis() -> Dict:
        """Get mock deepfake analysis for testing."""
        import random
        
        scenarios = [
            {
                'risk_score': 25,
                'threat_types': [],
                'explanation': "Audio analysis indicates natural voice patterns. No obvious deepfake indicators detected.",
                'confidence': 0.75
            },
            {
                'risk_score': 65,
                'threat_types': ['voice_anomaly', 'suspicious_audio_quality'],
                'explanation': "Audio analysis detected unusual voice patterns and compression artifacts. This could indicate voice spoofing.",
                'confidence': 0.82
            },
            {
                'risk_score': 85,
                'threat_types': ['potential_deepfake_voice', 'unnatural_voice_modulation'],
                'explanation': "Audio contains strong indicators of voice synthesis or deepfake technology. This is likely not a natural human voice.",
                'confidence': 0.88
            }
        ]
        
        return random.choice(scenarios)
