#!/usr/bin/env python
"""
Enhanced training script for small datasets
Incorporates best practices for preventing overfitting:
- Aggressive data augmentation
- L2 regularization
- Early stopping
- Dropout
- Learning rate scheduling
- Class weighting for imbalanced data
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import logging
from pathlib import Path
import json
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.cnn_model import DeepfakeCNN
from training.improved_dataset import ImprovedDeepfakeAudioDataset

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class EnhancedModelTrainer:
    """Training with best practices for small datasets."""
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'auto',
        checkpoint_dir: str = 'backend/models'
    ):
        """Initialize trainer."""
        if device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        self.model = model.to(self.device)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Using device: {self.device}")
        
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'learning_rate': []
        }
        self.best_val_loss = float('inf')
        self.best_epoch = 0
        self.no_improve_count = 0
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 100,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-3,  # Stronger L2 regularization for small datasets
        patience: int = 15,
        class_weights: torch.Tensor = None
    ) -> nn.Module:
        """
        Train the model with enhanced techniques for small datasets.
        
        Args:
            train_loader: Training data
            val_loader: Validation data
            epochs: Maximum epochs
            learning_rate: Initial learning rate
            weight_decay: L2 regularization (stronger for small datasets)
            patience: Early stopping patience
            class_weights: Weights for imbalanced classes
        """
        
        # Use weighted loss for imbalanced datasets
        if class_weights is not None:
            class_weights = class_weights.to(self.device)
        
        criterion = nn.BCEWithLogitsLoss(
            pos_weight=class_weights if class_weights is not None else None
        )
        
        # Optimizer with strong regularization
        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,  # L2 penalty on all weights
            betas=(0.9, 0.999)
        )
        
        # Aggressive learning rate scheduling for small datasets
        scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer,
            T_0=10,  # Restart every 10 epochs
            T_mult=2,  # Double the period each restart
            eta_min=1e-6
        )
        
        logger.info(f"Starting training: {epochs} epochs, lr={learning_rate}, weight_decay={weight_decay}")
        logger.info(f"Dataset sizes: {len(train_loader.dataset)} train, {len(val_loader.dataset)} val")
        
        for epoch in range(epochs):
            # Training phase
            train_loss, train_acc = self._train_epoch(train_loader, criterion, optimizer)
            
            # Validation phase
            val_loss, val_acc = self._validate_epoch(val_loader, criterion)
            
            # Record history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_acc'].append(val_acc)
            self.history['learning_rate'].append(optimizer.param_groups[0]['lr'])
            
            # Log progress
            logger.info(
                f"Epoch {epoch:3d} | "
                f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.3f} | "
                f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.3f} | "
                f"LR: {optimizer.param_groups[0]['lr']:.2e}"
            )
            
            # Early stopping with checkpoint saving
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_epoch = epoch
                self.no_improve_count = 0
                self._save_checkpoint(epoch, val_loss)
                logger.info(f"✓ Best model saved! (val_loss: {val_loss:.4f})")
            else:
                self.no_improve_count += 1
                if self.no_improve_count >= patience:
                    logger.info(
                        f"Early stopping triggered after {epoch - self.best_epoch} epochs "
                        f"without improvement. Best val_loss: {self.best_val_loss:.4f}"
                    )
                    break
            
            # Learning rate schedule
            scheduler.step()
        
        logger.info(f"Training complete. Best epoch: {self.best_epoch}, Best val_loss: {self.best_val_loss:.4f}")
        return self.model
    
    def _train_epoch(self, loader: DataLoader, criterion, optimizer) -> tuple:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for mel_specs, labels in loader:
            mel_specs = mel_specs.to(self.device)
            labels = labels.to(self.device).unsqueeze(-1)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = self.model(mel_specs)
            loss = criterion(outputs, labels)
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            # Calculate accuracy
            probs = torch.sigmoid(outputs).detach()
            preds = (probs > 0.5).long()
            correct += (preds == labels.long()).sum().item()
            total += labels.size(0)
        
        avg_loss = total_loss / len(loader)
        accuracy = correct / total if total > 0 else 0
        
        return avg_loss, accuracy
    
    def _validate_epoch(self, loader: DataLoader, criterion) -> tuple:
        """Validate for one epoch."""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for mel_specs, labels in loader:
                mel_specs = mel_specs.to(self.device)
                labels = labels.to(self.device).unsqueeze(-1)
                
                outputs = self.model(mel_specs)
                loss = criterion(outputs, labels)
                
                total_loss += loss.item()
                
                probs = torch.sigmoid(outputs)
                preds = (probs > 0.5).long()
                correct += (preds == labels.long()).sum().item()
                total += labels.size(0)
        
        avg_loss = total_loss / len(loader)
        accuracy = correct / total if total > 0 else 0
        
        return avg_loss, accuracy
    
    def _save_checkpoint(self, epoch: int, val_loss: float):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'val_loss': val_loss,
            'timestamp': datetime.now().isoformat()
        }
        
        path = self.checkpoint_dir / 'cnn_deepfake_best.pt'
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved to {path}")


def main():
    """Main training script."""
    
    logger.info("=" * 60)
    logger.info("ENHANCED TRAINING FOR SMALL DATASETS")
    logger.info("=" * 60)
    
    # Load dataset with augmentation
    logger.info("Loading dataset with aggressive augmentation...")
    dataset = ImprovedDeepfakeAudioDataset(
        data_dir='backend/training/data/audio',
        output_dir='backend/models',
        augment=True,
        n_augmentations=3,  # 3 augmented versions per sample
        duration=3.0,
        sr=16000,
        n_mels=128
    )
    
    # Count classes for weighting
    labels = [label for _, label in dataset.samples]
    n_scam = sum(labels)
    n_genuine = len(labels) - n_scam
    
    # Calculate class weights (balance imbalanced data)
    total = len(labels)
    weight_genuine = total / (2 * n_genuine) if n_genuine > 0 else 1.0
    weight_scam = total / (2 * n_scam) if n_scam > 0 else 1.0
    class_weight = torch.tensor(weight_scam / weight_genuine)
    
    logger.info(f"Class distribution: {n_genuine} genuine, {n_scam} scam")
    logger.info(f"Class weights (scam/genuine): {class_weight:.2f}")
    
    # Split dataset (80/20)
    train_size = int(0.8 * len(dataset.samples))
    val_size = len(dataset.samples) - train_size
    
    train_dataset, val_dataset = random_split(
        dataset,
        [train_size * 3 + val_size, val_size * 3],  # Accounts for augmentation
        generator=torch.Generator().manual_seed(42)
    )
    
    # Create loaders with aggressive batch preprocessing
    train_loader = DataLoader(
        train_dataset,
        batch_size=4,
        shuffle=True,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=4,
        shuffle=False,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    
    # Initialize model and trainer
    model = DeepfakeCNN()
    trainer = EnhancedModelTrainer(
        model=model,
        device='auto',
        checkpoint_dir='backend/models'
    )
    
    # Train with enhanced techniques
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=100,  # Allow up to 100 with early stopping
        learning_rate=0.001,
        weight_decay=1e-3,  # Strong L2 regularization
        patience=15,  # Stop after 15 epochs without improvement
        class_weights=class_weight
    )
    
    # Save training history
    history_path = Path('backend/models/training_history.json')
    with open(history_path, 'w') as f:
        json.dump(trainer.history, f, indent=2)
    logger.info(f"Training history saved to {history_path}")
    
    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
