"""
Training module for CNN deepfake detector

Usage:
    from training.train_cnn import ModelTrainer, create_dataloaders
    from training.dataset import DeepfakeAudioDataset
"""

from training.dataset import DeepfakeAudioDataset, SimpleAudioDataset
from training.train_cnn import ModelTrainer, create_dataloaders

__all__ = [
    'DeepfakeAudioDataset',
    'SimpleAudioDataset',
    'ModelTrainer',
    'create_dataloaders'
]
