"""
Configuration for CNN training and inference
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioConfig:
    """Audio processing configuration."""
    
    sample_rate: int = 16000
    n_mels: int = 128
    n_fft: int = 2048
    hop_length: int = 512


@dataclass
class TrainingConfig:
    """Training hyperparameters."""
    
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 0.001
    weight_decay: float = 1e-4
    dropout_rate: float = 0.5
    patience: int = 10  # Early stopping patience


@dataclass
class DataConfig:
    """Data configuration."""
    
    data_dir: str = 'training/data'
    train_split: float = 0.8
    num_workers: int = 4
    augment: bool = True


@dataclass
class ModelConfig:
    """Model configuration."""
    
    model_type: str = 'standard'  # 'standard' or 'lightweight'
    checkpoint_dir: str = 'models'
    best_model_name: str = 'cnn_deepfake_best.pt'
    final_model_name: str = 'cnn_deepfake_final.pt'


@dataclass
class InferenceConfig:
    """Inference configuration."""
    
    device: str = 'auto'  # 'cuda', 'cpu', or 'auto'
    model_path: Optional[str] = 'models/cnn_deepfake_best.pt'
    use_lightweight: bool = False
    confidence_threshold: float = 0.5  # Confidence threshold for predictions
