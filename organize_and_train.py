"""
Script to organize audio files into proper folder structure and train CNN
"""

import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
data_root = Path('backend/training/data')
audio_dir = data_root / 'audio'

# Create organized folder structure
genuine_dir = data_root / 'genuine'
scam_dir = data_root / 'scam'

genuine_dir.mkdir(exist_ok=True, parents=True)
scam_dir.mkdir(exist_ok=True, parents=True)

print("Organizing dataset...")
print("=" * 50)

# Count files
genuine_count = 0
scam_count = 0

# Organize files
for file in audio_dir.iterdir():
    if file.suffix.lower() in ['.wav', '.mp3']:
        if file.stem.startswith('genuine_'):
            # Copy WAV version only to avoid duplicates
            if file.suffix.lower() == '.wav':
                shutil.copy(file, genuine_dir / file.name)
                genuine_count += 1
                logger.info(f"Moved: {file.name} -> genuine/")
        
        elif file.stem.startswith('scam_'):
            # Copy WAV version only
            if file.suffix.lower() == '.wav':
                shutil.copy(file, scam_dir / file.name)
                scam_count += 1
                logger.info(f"Moved: {file.name} -> scam/")

print("\n" + "=" * 50)
print(f"✓ Organization complete!")
print(f"  Genuine samples: {genuine_count}")
print(f"  Scam samples: {scam_count}")
print(f"  Total samples: {genuine_count + scam_count}")
print("=" * 50)

# Now train the model
print("\nStarting CNN training...")
print("=" * 50)

import sys
sys.path.insert(0, 'backend')

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from app.models.cnn_model import DeepfakeCNN
from training.dataset import DeepfakeAudioDataset
from training.train_cnn import ModelTrainer

# Load dataset
print("\nLoading dataset...")
dataset = DeepfakeAudioDataset(
    data_dir=str(data_root),
    sr=16000,
    n_mels=128,
    duration=3.0,  # 3-second clips
    augment=True
)

print(f"Dataset loaded: {len(dataset)} samples")

# Split into train/val
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")

# Create model
print("\nCreating CNN model...")
model = DeepfakeCNN()

# Train
print("Training model (this may take a few minutes)...")
print("=" * 50)

trainer = ModelTrainer(model, device='cpu', checkpoint_dir='backend/models')
trained_model = trainer.train(
    train_loader=train_loader,
    val_loader=val_loader,
    epochs=30,
    learning_rate=0.001,
    weight_decay=1e-4,
    patience=10
)

# Save model
model_path = Path('backend/models/cnn_deepfake_best.pt')
torch.save(trained_model.state_dict(), model_path)

print("\n" + "=" * 50)
print(f"✓ Training complete!")
print(f"✓ Model saved to: {model_path}")
print("=" * 50)

# Print training history
print("\nTraining History:")
for key, values in trainer.history.items():
    if values:
        final_val = values[-1]
        print(f"  {key}: {final_val:.4f}")
