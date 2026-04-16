"""
Dataset classes for training CNN deepfake detector
Handles loading and preprocessing audio files
"""

import torch
from torch.utils.data import Dataset
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available")


class DeepfakeAudioDataset(Dataset):
    """
    PyTorch Dataset for deepfake detection from audio files.
    
    Expected directory structure (supports both naming conventions):
    data/
        real/ (or genuine/)
            speaking_001.wav
            speaking_002.wav
            ...
        fake/ (or scam/)
            synthesized_001.wav
            synthesized_002.wav
            ...
    
    Labels: 0 = genuine/real speech, 1 = scam/deepfake/synthetic speech
    """
    
    def __init__(
        self,
        data_dir: str,
        sr: int = 16000,
        n_mels: int = 128,
        duration: Optional[float] = None,
        augment: bool = False
    ):
        """
        Initialize dataset.
        
        Args:
            data_dir: Root directory containing 'real' and 'fake' subdirectories
            sr: Sample rate for audio loading
            n_mels: Number of mel frequency bins
            duration: Target duration in seconds (pads/truncates if set)
            augment: Enable data augmentation
        """
        self.data_dir = Path(data_dir)
        self.sr = sr
        self.n_mels = n_mels
        self.duration = duration
        self.augment = augment
        self.audio_paths: List[Tuple[Path, int]] = []
        
        if not LIBROSA_AVAILABLE:
            raise RuntimeError("librosa is required for audio loading")
        
        self._load_file_list()
        
        if len(self.audio_paths) == 0:
            raise ValueError(
                f"No audio files found in {data_dir}. "
                f"Expected structure: {data_dir}/(real|genuine)/ and {data_dir}/(fake|scam)/"
            )
        
        logger.info(
            f"Loaded dataset: {len(self.audio_paths)} files "
            f"({self._count_by_label(0)} genuine, {self._count_by_label(1)} scam)"
        )
    
    def _load_file_list(self):
        """Scan directory for audio files."""
        
        audio_extensions = {'.wav', '.mp3', '.flac', '.ogg'}
        
        # Try real/fake folder names first
        real_dir = self.data_dir / 'real'
        fake_dir = self.data_dir / 'fake'
        
        # Also try genuine/scam folder names
        genuine_dir = self.data_dir / 'genuine'
        scam_dir = self.data_dir / 'scam'
        
        # Load real/genuine audio (label 0)
        for source_dir in [real_dir, genuine_dir]:
            if source_dir.exists():
                for audio_file in source_dir.iterdir():
                    if audio_file.suffix.lower() in audio_extensions:
                        self.audio_paths.append((audio_file, 0))
        
        # Load fake/scam audio (label 1)
        for source_dir in [fake_dir, scam_dir]:
            if source_dir.exists():
                for audio_file in source_dir.iterdir():
                    if audio_file.suffix.lower() in audio_extensions:
                        self.audio_paths.append((audio_file, 1))
    
    def _count_by_label(self, label: int) -> int:
        """Count files by label."""
        return sum(1 for _, l in self.audio_paths if l == label)
    
    def __len__(self) -> int:
        """Total number of samples."""
        return len(self.audio_paths)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a single sample.
        
        Returns:
            Tuple of (spectrogram, label)
            - spectrogram: (1, n_mels, time_steps) - normalized mel spectrogram
            - label: 0 (real) or 1 (fake)
        """
        audio_path, label = self.audio_paths[idx]
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sr)
            
            # Pad or truncate to target duration
            if self.duration is not None:
                target_samples = int(self.duration * self.sr)
                if len(y) < target_samples:
                    # Pad with zeros
                    y = np.pad(y, (0, target_samples - len(y)), mode='constant')
                else:
                    # Truncate
                    y = y[:target_samples]
            
            # Apply augmentation if enabled
            if self.augment and np.random.random() > 0.5:
                y = self._augment_audio(y)
            
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
            
            # Pad or truncate to fixed time steps (ensure consistent size)
            # For 3 seconds at sr=16000, hop_length=512: ~94 time steps
            target_time_steps = int(np.ceil((self.duration * self.sr - 2048) / 512)) + 1
            if mel_spec_db.shape[1] < target_time_steps:
                # Pad with silence
                mel_spec_db = np.pad(
                    mel_spec_db,
                    ((0, 0), (0, target_time_steps - mel_spec_db.shape[1])),
                    mode='constant',
                    constant_values=-100  # Silence in dB
                )
            else:
                # Truncate
                mel_spec_db = mel_spec_db[:, :target_time_steps]
            
            # Normalize
            mel_spec_normalized = (
                (mel_spec_db - mel_spec_db.mean()) /
                (mel_spec_db.std() + 1e-5)
            )
            
            # Convert to tensor with channel dimension
            spectrogram = torch.from_numpy(mel_spec_normalized).float()
            spectrogram = spectrogram.unsqueeze(0)  # (1, n_mels, time_steps)
            
            label_tensor = torch.tensor(label, dtype=torch.float32)
            
            return spectrogram, label_tensor
            
        except Exception as e:
            logger.error(f"Error loading {audio_path}: {e}")
            # Return silence on error
            dummy_spec = torch.zeros((1, self.n_mels, 100))
            return dummy_spec, torch.tensor(0.0, dtype=torch.float32)
    
    def _augment_audio(self, y: np.ndarray) -> np.ndarray:
        """
        Apply data augmentation to audio.
        
        Techniques:
        - Time stretching (speed variation)
        - Pitch shifting
        - Adding Gaussian noise
        """
        
        if np.random.random() > 0.5:
            # Time stretching: vary playback speed slightly
            rate = np.random.uniform(0.95, 1.05)
            y = librosa.effects.time_stretch(y, rate=rate)
        
        if np.random.random() > 0.5:
            # Pitch shifting
            n_steps = np.random.randint(-2, 3)
            y = librosa.effects.pitch_shift(y, sr=self.sr, n_steps=n_steps)
        
        if np.random.random() > 0.5:
            # Add Gaussian noise
            noise_factor = np.random.uniform(0.0, 0.01)
            noise = np.random.randn(len(y))
            y = y + noise_factor * noise
        
        return y


class SimpleAudioDataset(Dataset):
    """
    Simpler dataset that works with a CSV file mapping paths to labels.
    
    CSV format:
    path,label
    /path/to/audio1.wav,0
    /path/to/audio2.wav,1
    ...
    """
    
    def __init__(
        self,
        csv_file: str,
        sr: int = 16000,
        n_mels: int = 128
    ):
        """
        Initialize from CSV file.
        
        Args:
            csv_file: Path to CSV file with columns: path, label
            sr: Sample rate
            n_mels: Number of mel bins
        """
        self.sr = sr
        self.n_mels = n_mels
        self.samples: List[Tuple[Path, int]] = []
        
        if LIBROSA_AVAILABLE:
            self._load_from_csv(csv_file)
        else:
            raise RuntimeError("librosa is required")
    
    def _load_from_csv(self, csv_file: str):
        """Load sample list from CSV."""
        import csv
        
        csv_path = Path(csv_file)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                audio_path = Path(row['path'])
                label = int(row['label'])
                
                if audio_path.exists():
                    self.samples.append((audio_path, label))
        
        logger.info(f"Loaded {len(self.samples)} samples from {csv_file}")
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get sample at index."""
        audio_path, label = self.samples[idx]
        
        try:
            y, sr = librosa.load(audio_path, sr=self.sr)
            
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, n_mels=self.n_mels
            )
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            mel_spec_normalized = (
                (mel_spec_db - mel_spec_db.mean()) /
                (mel_spec_db.std() + 1e-5)
            )
            
            spectrogram = torch.from_numpy(mel_spec_normalized).float()
            spectrogram = spectrogram.unsqueeze(0)
            
            return spectrogram, torch.tensor(label, dtype=torch.float32)
            
        except Exception as e:
            logger.error(f"Error loading {audio_path}: {e}")
            return torch.zeros((1, self.n_mels, 100)), torch.tensor(0.0)
