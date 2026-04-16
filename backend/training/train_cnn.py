"""
Training script for CNN deepfake detector
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import logging
from pathlib import Path
from typing import Tuple
import json
from datetime import datetime

# Import from project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.cnn_model import DeepfakeCNN, LightweightDeepfakeCNN
from training.dataset import DeepfakeAudioDataset

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class ModelTrainer:
    """Handles training loop for deepfake CNN detector."""
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'auto',
        checkpoint_dir: str = 'models'
    ):
        """
        Initialize trainer.
        
        Args:
            model: PyTorch model to train
            device: 'cuda', 'cpu', or 'auto'
            checkpoint_dir: Directory to save checkpoints
        """
        if device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        self.model = model.to(self.device)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        logger.info(f"Using device: {self.device}")
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 50,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-4,
        patience: int = 10
    ) -> nn.Module:
        """
        Train the model.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            epochs: Number of epochs
            learning_rate: Initial learning rate
            weight_decay: L2 regularization
            patience: Early stopping patience
            
        Returns:
            Trained model
        """
        
        # Optimizer and loss
        optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        criterion = nn.BCELoss()
        
        # Learning rate scheduler
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,
            patience=3
        )
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        logger.info(f"Starting training for {epochs} epochs...")
        logger.info(f"Optimizer: Adam, LR: {learning_rate}, Weight decay: {weight_decay}")
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_idx, (spectrograms, labels) in enumerate(train_loader):
                spectrograms = spectrograms.to(self.device)
                labels = labels.unsqueeze(1).to(self.device)
                
                # Forward pass
                optimizer.zero_grad()
                outputs = self.model(spectrograms)
                loss = criterion(outputs, labels)
                
                # Backward pass
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                
                train_loss += loss.item()
                
                # Calculate accuracy
                predicted = (outputs > 0.5).float()
                train_correct += (predicted == labels).sum().item()
                train_total += labels.size(0)
                
                if (batch_idx + 1) % max(1, len(train_loader) // 5) == 0:
                    avg_loss = train_loss / (batch_idx + 1)
                    logger.info(
                        f"Epoch [{epoch+1}/{epochs}] Batch [{batch_idx+1}/{len(train_loader)}] "
                        f"Loss: {avg_loss:.4f}"
                    )
            
            avg_train_loss = train_loss / len(train_loader)
            avg_train_acc = train_correct / train_total if train_total > 0 else 0
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for spectrograms, labels in val_loader:
                    spectrograms = spectrograms.to(self.device)
                    labels = labels.unsqueeze(1).to(self.device)
                    
                    outputs = self.model(spectrograms)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item()
                    
                    predicted = (outputs > 0.5).float()
                    val_correct += (predicted == labels).sum().item()
                    val_total += labels.size(0)
            
            avg_val_loss = val_loss / len(val_loader)
            avg_val_acc = val_correct / val_total if val_total > 0 else 0
            
            # Log epoch results
            logger.info(
                f"Epoch [{epoch+1}/{epochs}] "
                f"Train Loss: {avg_train_loss:.4f}, Train Acc: {avg_train_acc:.4f} | "
                f"Val Loss: {avg_val_loss:.4f}, Val Acc: {avg_val_acc:.4f}"
            )
            
            # Store history
            self.history['train_loss'].append(avg_train_loss)
            self.history['val_loss'].append(avg_val_loss)
            self.history['train_acc'].append(avg_train_acc)
            self.history['val_acc'].append(avg_val_acc)
            
            # Update learning rate
            scheduler.step(avg_val_loss)
            
            # Save best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                
                checkpoint_path = self.checkpoint_dir / 'cnn_deepfake_best.pt'
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'train_loss': avg_train_loss,
                    'val_loss': avg_val_loss,
                    'train_acc': avg_train_acc,
                    'val_acc': avg_val_acc,
                }, checkpoint_path)
                
                logger.info(f"✓ Saved best model at epoch {epoch+1} to {checkpoint_path}")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= patience:
                logger.info(
                    f"Early stopping triggered at epoch {epoch+1} "
                    f"(no improvement for {patience} epochs)"
                )
                break
        
        # Save final model
        final_checkpoint = self.checkpoint_dir / 'cnn_deepfake_final.pt'
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'history': self.history
        }, final_checkpoint)
        logger.info(f"✓ Saved final model to {final_checkpoint}")
        
        # Save training history
        history_file = self.checkpoint_dir / 'training_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
        logger.info(f"✓ Saved training history to {history_file}")
        
        return self.model
    
    def get_model_info(self) -> dict:
        """Get model information."""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'device': self.device,
            'model_class': self.model.__class__.__name__
        }


def create_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    train_split: float = 0.8,
    augment: bool = True
) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation dataloaders.
    
    Args:
        data_dir: Root data directory
        batch_size: Batch size
        num_workers: Number of worker processes
        train_split: Train/val split ratio
        augment: Enable augmentation
        
    Returns:
        Tuple of (train_loader, val_loader)
    """
    
    logger.info(f"Loading dataset from {data_dir}...")
    dataset = DeepfakeAudioDataset(
        data_dir,
        augment=augment
    )
    
    # Split dataset
    train_size = int(len(dataset) * train_split)
    val_size = len(dataset) - train_size
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset,
        [train_size, val_size]
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    logger.info(
        f"Dataset split: {train_size} train, {val_size} val "
        f"(batch_size={batch_size})"
    )
    
    return train_loader, val_loader


def main():
    """Main training entrypoint."""
    
    # Configuration
    config = {
        'data_dir': 'training/data',
        'checkpoint_dir': 'models',
        'batch_size': 32,
        'epochs': 50,
        'learning_rate': 0.001,
        'device': 'auto',
        'model_type': 'standard',  # 'standard' or 'lightweight'
        'use_augmentation': True,
        'train_split': 0.8
    }
    
    logger.info("=" * 60)
    logger.info("CNN Deepfake Detector Training")
    logger.info("=" * 60)
    logger.info(f"Config: {json.dumps(config, indent=2)}")
    
    # Create dataloaders
    try:
        train_loader, val_loader = create_dataloaders(
            config['data_dir'],
            batch_size=config['batch_size'],
            train_split=config['train_split'],
            augment=config['use_augmentation']
        )
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        logger.info("\nTo train, organize your audio files:")
        logger.info("  data/")
        logger.info("    real/")
        logger.info("      audio_1.wav")
        logger.info("      audio_2.wav")
        logger.info("      ...")
        logger.info("    fake/")
        logger.info("      synth_1.wav")
        logger.info("      synth_2.wav")
        logger.info("      ...")
        return
    
    # Create model
    if config['model_type'] == 'lightweight':
        model = LightweightDeepfakeCNN()
    else:
        model = DeepfakeCNN()
    
    # Create trainer
    trainer = ModelTrainer(
        model,
        device=config['device'],
        checkpoint_dir=config['checkpoint_dir']
    )
    
    logger.info(f"Model info: {json.dumps(trainer.get_model_info(), indent=2)}")
    
    # Train
    trainer.train(
        train_loader,
        val_loader,
        epochs=config['epochs'],
        learning_rate=config['learning_rate']
    )
    
    logger.info("=" * 60)
    logger.info("Training completed!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
