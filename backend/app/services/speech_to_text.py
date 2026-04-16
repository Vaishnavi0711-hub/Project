"""
Speech-to-text service using OpenAI Whisper
"""

import logging
import asyncio
from typing import Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
    logger.info("✓ Whisper library available for audio transcription")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Install with: pip install openai-whisper")

try:
    import librosa
    LIBROSA_AVAILABLE = True
    logger.info("✓ Librosa available for audio loading")
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("Librosa not available. Install with: pip install librosa")

try:
    from scipy.io import wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("Scipy not available")

class SpeechToTextService:
    """
    Converts audio to text using OpenAI Whisper.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the speech-to-text service.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Load Whisper model."""
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available - cannot transcribe real audio")
            return
        
        try:
            logger.info(f"Loading Whisper {self.model_name} model for audio transcription...")
            self.model = whisper.load_model(self.model_name)
            logger.info(f"✓ Whisper {self.model_name} model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    def _load_audio(self, audio_path: str) -> Optional[np.ndarray]:
        """
        Load audio file into numpy array.
        Tries multiple methods: librosa first, then scipy for WAV files.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Audio as numpy array (mono, 16kHz) or None if failed
        """
        
        try:
            if LIBROSA_AVAILABLE:
                logger.info("Loading audio with librosa...")
                # Load audio, convert to mono, resample to 16kHz
                audio, _ = librosa.load(audio_path, sr=16000, mono=True)
                logger.info(f"✓ Audio loaded with librosa: {len(audio)} samples")
                return audio
        except Exception as e:
            logger.warning(f"Librosa loading failed: {e}")
        
        # Fallback: try scipy for WAV files
        try:
            if SCIPY_AVAILABLE and audio_path.lower().endswith('.wav'):
                logger.info("Loading WAV audio with scipy...")
                sr, audio = wavfile.read(audio_path)
                # Convert to mono if stereo
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                # Normalize to float32
                if audio.dtype == np.int16:
                    audio = audio.astype(np.float32) / 32768.0
                logger.info(f"✓ Audio loaded with scipy: {len(audio)} samples at {sr}Hz")
                return audio
        except Exception as e:
            logger.warning(f"Scipy loading failed: {e}")
        
        return None
    
    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_path)
    
    def _transcribe_sync(self, audio_path: str) -> str:
        """
        Synchronous transcription (runs in thread pool).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text (real transcription from audio)
        """
        
        # Verify file exists with detailed diagnostics
        audio_path_obj = Path(audio_path)
        logger.info(f"Transcription request received for: {audio_path}")
        logger.info(f"  Path exists: {audio_path_obj.exists()}")
        logger.info(f"  Is file: {audio_path_obj.is_file()}")
        logger.info(f"  Absolute path: {audio_path_obj.absolute()}")
        logger.info(f"  Parent dir exists: {audio_path_obj.parent.exists()}")
        
        if audio_path_obj.parent.exists():
            logger.info(f"  Files in temp dir: {list(audio_path_obj.parent.glob('*'))}")
        
        if not audio_path_obj.exists():
            logger.error(f"Audio file not found: {audio_path}")
            logger.error(f"Absolute path attempted: {audio_path_obj.absolute()}")
            return "Audio file not found - temporary file may have been deleted"
        
        # Use REAL transcription
        if not WHISPER_AVAILABLE or self.model is None:
            logger.error("Whisper model not available - cannot transcribe audio")
            return "Whisper model not loaded. Please ensure openai-whisper is installed."
        
        try:
            logger.info(f"Transcribing audio file: {audio_path}")
            logger.info(f"File size: {audio_path_obj.stat().st_size} bytes")
            
            # Load audio to numpy array (avoids FFmpeg dependency)
            audio = self._load_audio(audio_path)
            if audio is None:
                logger.error("Failed to load audio file with any available method")
                return "Failed to load audio - ensure audio file format is supported"
            
            # Transcribe using Whisper with numpy array
            logger.info("Passing audio to Whisper for transcription...")
            result = self.model.transcribe(audio, language="en", verbose=False)
            text = result["text"].strip()
            
            logger.info(f"✓ Transcription complete")
            logger.info(f"  Length: {len(text)} characters")
            logger.info(f"  Preview: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            if not text:
                logger.warning("Transcription resulted in empty text")
                return "Could not transcribe audio - no speech detected"
            
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return f"Transcription failed: {str(e)}"
