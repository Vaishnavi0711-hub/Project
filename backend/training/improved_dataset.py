"""
Enhanced dataset with aggressive augmentation for small datasets
Addresses overfitting when training on limited audio samples
"""

import torch
import librosa
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class AugmentationPipeline:
    """
    Aggressive audio augmentation to prevent overfitting on small datasets.
    Each sample is augmented in multiple ways to increase effective dataset size.
    """
    
    def __init__(self, n_augmentations: int = 3):
        """
        Args:
            n_augmentations: Number of augmented versions per sample
        """
        self.n_augmentations = n_augmentations
    
    def pitch_shift(self, y: np.ndarray, sr: int, shift_range: int = 4) -> np.ndarray:
        """
        Shift pitch randomly. Helps model learn pitch-invariant features.
        
        Args:
            y: Audio samples
            sr: Sample rate
            shift_range: Number of semitones to shift (±)
        """
        shift = np.random.randint(-shift_range, shift_range + 1)
        return librosa.effects.pitch_shift(y, sr=sr, n_steps=shift)
    
    def time_stretch(self, y: np.ndarray, rate_range: Tuple[float, float] = (0.9, 1.1)) -> np.ndarray:
        """
        Stretch time. Helps model learn speed-invariant features.
        
        Args:
            y: Audio samples
            rate_range: Speed range (0.9x to 1.1x)
        """
        rate = np.random.uniform(rate_range[0], rate_range[1])
        return librosa.effects.time_stretch(y, rate=rate)
    
    def add_noise(self, y: np.ndarray, noise_std: float = 0.003) -> np.ndarray:
        """
        Add Gaussian noise. Helps model robustness.
        
        Args:
            y: Audio samples
            noise_std: Standard deviation of noise
        """
        noise = np.random.normal(0, noise_std, len(y))
        return y + noise
    
    def crop_and_concatenate(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Crop random sections and mix. Increases variety.
        
        Args:
            y: Audio samples
            sr: Sample rate
        """
        # Take a random 80% of the audio
        max_start = int(0.2 * len(y))
        start = np.random.randint(0, max(1, max_start))
        end = min(len(y), start + int(0.8 * len(y)))
        return y[start:end]
    
    def augment(self, y: np.ndarray, sr: int) -> List[np.ndarray]:
        """
        Apply multiple augmentations to create n_augmentations versions of same audio.
        
        Args:
            y: Audio samples
            sr: Sample rate
            
        Returns:
            List of augmented audio arrays
        """
        augmented = [y]  # Original
        
        for _ in range(self.n_augmentations):
            aug = y.copy()
            
            # Random combination of augmentations
            if np.random.random() > 0.5:
                aug = self.pitch_shift(aug, sr, shift_range=3)
            
            if np.random.random() > 0.5:
                aug = self.time_stretch(aug, rate_range=(0.95, 1.05))
            
            if np.random.random() > 0.7:
                aug = self.add_noise(aug, noise_std=0.002)
            
            if np.random.random() > 0.6:
                aug = self.crop_and_concatenate(aug, sr)
            
            augmented.append(aug)
        
        return augmented


class ImprovedDeepfakeAudioDataset(torch.utils.data.Dataset):
    """
    Improved dataset with built-in augmentation.
    For small datasets, this is critical to prevent overfitting.
    """
    
    def __init__(
        self,
        data_dir: str = 'backend/training/data/audio',
        output_dir: str = 'backend/models',
        augment: bool = True,
        n_augmentations: int = 3,
        duration: float = 3.0,
        sr: int = 16000,
        n_mels: int = 128,
        seed: int = 42
    ):
        """
        Args:
            data_dir: Root directory containing 'genuine' and 'scam' folders
            output_dir: Where to save normalization statistics
            augment: Apply augmentation
            n_augmentations: Number of augmented versions per sample
            duration: Audio clip duration in seconds
            sr: Sample rate
            n_mels: Number of mel frequency bins
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)
        torch.manual_seed(seed)
        
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.augment = augment
        self.n_augmentations = n_augmentations if augment else 1
        self.duration = duration
        self.sr = sr
        self.n_mels = n_mels
        
        self.augmentation_pipeline = AugmentationPipeline(n_augmentations) if augment else None
        
        # Load file list
        self.samples = self._load_file_list()
        logger.info(f"Loaded {len(self.samples)} unique samples (×{self.n_augmentations} with augmentation = {len(self.samples) * self.n_augmentations} total)")
        
        # Compute and save normalization statistics
        self.mel_mean, self.mel_std = self._compute_normalization_stats()
        logger.info(f"Normalization stats: mean={self.mel_mean:.2f}, std={self.mel_std:.2f}")
    
    def _load_file_list(self) -> List[Tuple[str, int]]:
        """Load audio files and labels."""
        samples = []
        
        # Convert to absolute path for clarity
        data_dir = Path(self.data_dir).resolve()
        logger.info(f"Looking for audio files in: {data_dir}")
        
        # Method 1: Files directly in the directory with genuine/scam prefix
        # e.g., /data/audio/genuine_1.wav, /data/audio/scam_1.wav
        genuine_files = sorted(list(data_dir.glob('genuine*.wav')) + list(data_dir.glob('genuine*.mp3')))
        scam_files = sorted(list(data_dir.glob('scam*.wav')) + list(data_dir.glob('scam*.mp3')))
        
        if genuine_files or scam_files:
            logger.info(f"Found {len(genuine_files)} genuine files")
            for f in genuine_files:
                samples.append((str(f), 0))
            
            logger.info(f"Found {len(scam_files)} scam files")
            for f in scam_files:
                samples.append((str(f), 1))
        
        # Method 2: Files in subfolders
        # e.g., /data/genuine/*.wav and /data/scam/*.wav
        if not samples:
            for label, folder_names in [
                (0, ['genuine', 'real']),
                (1, ['scam', 'fake'])
            ]:
                for folder_name in folder_names:
                    folder_path = data_dir / folder_name
                    if folder_path.exists() and folder_path.is_dir():
                        files = sorted(
                            list(folder_path.glob('*.wav')) +
                            list(folder_path.glob('*.mp3')) +
                            list(folder_path.glob('*.flac')) +
                            list(folder_path.glob('*.ogg'))
                        )
                        
                        if files:
                            logger.info(f"Found {len(files)} {folder_name} files in {folder_path}")
                            for f in files:
                                samples.append((str(f), label))
                            break
        
        if not samples:
            raise ValueError(f"No audio files found in {data_dir}")
        
        logger.info(f"Total unique samples loaded: {len(samples)}")
        return samples
    
    def _compute_normalization_stats(self) -> Tuple[float, float]:
        """Compute mean and std of mel spectrograms for normalization."""
        mel_values = []
        
        for audio_path, _ in self.samples[:5]:  # Sample first 5 files
            try:
                y, _ = librosa.load(audio_path, sr=self.sr, duration=self.duration)
                mel = librosa.feature.melspectrogram(y=y, sr=self.sr, n_mels=self.n_mels)
                mel_db = librosa.power_to_db(mel, ref=np.max)
                mel_values.extend(mel_db.flatten())
            except Exception as e:
                logger.warning(f"Error loading {audio_path}: {e}")
        
        if mel_values:
            return float(np.mean(mel_values)), float(np.std(mel_values))
        else:
            logger.warning("Could not compute stats, using defaults")
            return -40.0, 20.0
    
    def __len__(self) -> int:
        """Total number of samples (including augmented versions)."""
        return len(self.samples) * self.n_augmentations
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a sample with augmentation.
        
        Returns:
            (mel_spectrogram_tensor, label_tensor)
        """
        # Determine which original sample and which augmentation
        base_idx = idx // self.n_augmentations
        aug_idx = idx % self.n_augmentations
        
        audio_path, label = self.samples[base_idx]
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sr, duration=self.duration)
            
            # Pad or truncate to exact duration
            target_len = int(self.duration * self.sr)
            if len(y) < target_len:
                y = np.pad(y, (0, target_len - len(y)), mode='constant')
            else:
                y = y[:target_len]
            
            # Apply augmentation if enabled and not base sample
            if self.augment and aug_idx > 0 and self.augmentation_pipeline:
                augmented = self.augmentation_pipeline.augment(y, self.sr)
                y = augmented[aug_idx]  # Use the aug_idx-th augmentation
            
            # Extract mel spectrogram
            mel = librosa.feature.melspectrogram(
                y=y,
                sr=sr,
                n_mels=self.n_mels,
                n_fft=2048,
                hop_length=512
            )
            
            # Convert to dB scale
            mel_db = librosa.power_to_db(mel, ref=np.max)
            
            # Normalize using computed statistics
            mel_normalized = (mel_db - self.mel_mean) / (self.mel_std + 1e-5)
            
            # Fix time steps to 94 (3 seconds at 16kHz)
            target_time_steps = 94
            if mel_normalized.shape[1] < target_time_steps:
                mel_normalized = np.pad(
                    mel_normalized,
                    ((0, 0), (0, target_time_steps - mel_normalized.shape[1])),
                    mode='constant',
                    constant_values=-2.0  # Silence in normalized space
                )
            else:
                mel_normalized = mel_normalized[:, :target_time_steps]
            
            # Convert to tensor
            mel_tensor = torch.from_numpy(mel_normalized).unsqueeze(0).float()  # Add channel dim
            label_tensor = torch.tensor(label, dtype=torch.float32)
            
            return mel_tensor, label_tensor
        
        except Exception as e:
            logger.error(f"Error loading {audio_path}: {e}")
            # Return zeros as fallback
            return torch.zeros(1, self.n_mels, 94), torch.tensor(float(label), dtype=torch.float32)
