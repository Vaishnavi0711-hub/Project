#!/usr/bin/env python
"""
Quick script to retrain CNN with improved methods
Run this to improve model performance on your dataset
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == '__main__':
    # Import after path setup
    import torch
    from torch.utils.data import random_split, DataLoader
    from app.models.cnn_model import DeepfakeCNN
    from training.improved_dataset import ImprovedDeepfakeAudioDataset
    from training.train_enhanced import EnhancedModelTrainer
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("ENHANCED CNN TRAINING")
    print("="*60)
    print("\nKey improvements:")
    print("✓ Aggressive data augmentation (3x per sample)")
    print("✓ Strong L2 regularization (weight_decay=1e-3)")
    print("✓ Class weighting for imbalanced data")
    print("✓ Cosine annealing with warm restarts")
    print("✓ Early stopping with patience=15")
    print("✓ Gradient clipping to prevent instability")
    print("✓ Ensemble voting in inference")
    print("✓ More conservative risk thresholds")
    print("="*60 + "\n")
    
    # Load dataset
    logger.info("Loading dataset with aggressive augmentation...")
    
    dataset = ImprovedDeepfakeAudioDataset(
        data_dir='backend/training/data/audio',
        output_dir='backend/models',
        augment=True,
        n_augmentations=3,
        duration=3.0,
        sr=16000,
        n_mels=128
    )
    
    # Count classes
    labels = [label for _, label in dataset.samples]
    n_scam = sum(labels)
    n_genuine = len(labels) - n_scam
    
    # Class weights
    total = len(labels)
    weight_scam_over_genuine = (total / (2 * n_scam)) / (total / (2 * n_genuine)) if (n_genuine > 0 and n_scam > 0) else 1.0
    
    logger.info(f"Dataset: {n_genuine} genuine + {n_scam} scam = {total} samples")
    logger.info(f"With augmentation: {len(dataset)} total samples")
    logger.info(f"Class weight (scam/genuine): {weight_scam_over_genuine:.2f}")
    
    # Create train/val split based on original samples
    train_size = int(0.8 * len(dataset.samples))
    val_size = len(dataset.samples) - train_size
    
    # Split the unique samples
    gen = torch.Generator().manual_seed(42)
    indices = torch.randperm(len(dataset.samples), generator=gen).tolist()
    
    train_indices = set(indices[:train_size])
    val_indices = set(indices[train_size:])
    
    # Create subsets that respect the augmentation
    train_subset_indices = []
    val_subset_indices = []
    
    for i in range(len(dataset)):
        base_idx = i // dataset.n_augmentations
        if base_idx in train_indices:
            train_subset_indices.append(i)
        else:
            val_subset_indices.append(i)
    
    train_dataset = torch.utils.data.Subset(dataset, train_subset_indices)
    val_dataset = torch.utils.data.Subset(dataset, val_subset_indices)
    
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False, num_workers=0)
    
    # Initialize model and trainer
    model = DeepfakeCNN()
    trainer = EnhancedModelTrainer(
        model=model,
        device='auto',
        checkpoint_dir='backend/models'
    )
    
    # Train
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=100,
        learning_rate=0.001,
        weight_decay=1e-3,
        patience=15,
        class_weights=torch.tensor(weight_scam_over_genuine)
    )
    
    # Save history
    import json
    with open('backend/models/training_history.json', 'w') as f:
        json.dump(trainer.history, f, indent=2)
    
    print("\n" + "="*60)
    print("✓ TRAINING COMPLETE")
    print("="*60)
    print(f"Best model saved to: backend/models/cnn_deepfake_best.pt")
    print(f"Best epoch: {trainer.best_epoch}, Best val loss: {trainer.best_val_loss:.4f}")
    print("\nThe model will now:")
    print("• Use ensemble voting (4 predictions per audio)")
    print("• Be more conservative about flagging scams")
    print("• Have better generalization due to augmentation")
    print("• Provide consistent results for same audio")
    print("="*60 + "\n")
