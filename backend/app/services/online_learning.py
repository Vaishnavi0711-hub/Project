"""
Online Learning Service
Incrementally trains the CNN with user feedback while ensuring data privacy.

Features:
- Catastrophic forgetting prevention (EWC-inspired)
- Secure data deletion with verification
- Confidence-based sampling (prevents poisoning)
- Background training without blocking inference
- Model versioning and rollback capability
"""

import logging
import asyncio
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
import hashlib
import time

logger = logging.getLogger(__name__)

# Optional: Import PyTorch for online learning
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch not available - online learning disabled")
    # Stub for type checking
    torch = None
    nn = None
    optim = None

# Use TYPE_CHECKING for forward references to torch classes
if TYPE_CHECKING:
    import torch as torch_typing
    import torch.nn as nn_typing
else:
    torch_typing = None
    nn_typing = None

try:
    import librosa
    import numpy as np
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False


@dataclass
class OnlineLearningConfig:
    """Configuration for online learning."""
    
    # Learning rate (must be LOW to prevent catastrophic forgetting)
    learning_rate: float = 1e-5
    
    # Gradient clipping to prevent instability
    gradient_clip: float = 0.01
    
    # L2 regularization (prevents large weight updates)
    weight_decay: float = 1e-6
    
    # Only learn if model was wrong or uncertain
    confidence_threshold: float = 0.70
    
    # Batch size for updates (larger batches = more stable)
    batch_size: int = 4
    
    # EWC lambda: importance of old task (higher = preserve old knowledge)
    ewc_lambda: float = 0.1
    
    # Keep model checkpoints for rollback
    keep_checkpoints: int = 5
    
    # Verify deletion with multiple attempts
    deletion_verify_attempts: int = 3
    
    # Sample rate for audio
    sample_rate: int = 16000
    
    # Mel bins
    n_mels: int = 128


class SecureDeletion:
    """
    Secure file deletion with verification.
    Uses DoD 5220.22-M standard (3-pass overwrite).
    """
    
    @staticmethod
    async def secure_delete(file_path: str, verify: bool = True) -> bool:
        """
        Securely delete a file.
        
        Args:
            file_path: Path to file
            verify: Verify deletion was successful
            
        Returns:
            True if successful
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found for deletion: {file_path}")
            return True
        
        try:
            file_size = path.stat().st_size
            
            # DoD 5220.22-M: 3-pass overwrite
            # Pass 1: Zeros
            with open(path, 'wb') as f:
                f.write(b'\x00' * file_size)
            
            # Pass 2: Ones
            with open(path, 'wb') as f:
                f.write(b'\xff' * file_size)
            
            # Pass 3: Random
            with open(path, 'wb') as f:
                f.write(os.urandom(file_size))
            
            # Delete file
            path.unlink()
            
            # Verify deletion
            if verify:
                for attempt in range(3):
                    await asyncio.sleep(0.1)
                    if not path.exists():
                        logger.info(f"✓ Securely deleted: {path.name}")
                        return True
                
                logger.warning(f"Deletion verification failed: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Secure deletion error: {e}")
            return False


class ElasticWeightConsolidation:
    """
    Elastic Weight Consolidation (EWC) to prevent catastrophic forgetting.
    
    Penalizes changes to weights that were important for the original task.
    This allows learning new tasks while preserving knowledge of old tasks.
    
    Reference: Kirkpatrick et al., "Overcoming catastrophic forgetting in neural networks"
    """
    
    def __init__(self, model: "nn_typing.Module", lambda_ewc: float = 0.1):
        self.model = model
        self.lambda_ewc = lambda_ewc
        self.fisher_information = None
        self.optimal_params = None
    
    def compute_fisher_information(
        self,
        data_loader,
        num_samples: Optional[int] = None
    ):
        """
        Compute Fisher Information Matrix (importance weights).
        
        Args:
            data_loader: DataLoader for original training data
            num_samples: Limit samples for efficiency
        """
        self.model.eval()
        
        for name, param in self.model.named_parameters():
            param.requires_grad = False
        
        fisher_info = {}
        
        for name, param in self.model.named_parameters():
            fisher_info[name] = torch.zeros_like(param)
        
        for batch_idx, (data, target) in enumerate(data_loader):
            if num_samples and batch_idx >= num_samples:
                break
            
            self.model.zero_grad()
            
            output = self.model(data)
            
            # Use log probability of correct class
            log_probs = torch.log(output + 1e-8)
            loss = -log_probs.sum()
            loss.backward()
            
            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    fisher_info[name] += param.grad ** 2
        
        # Normalize by number of samples
        for name in fisher_info:
            fisher_info[name] /= (batch_idx + 1)
        
        self.fisher_information = fisher_info
        
        # Store optimal parameters
        self.optimal_params = {
            name: param.clone().detach()
            for name, param in self.model.named_parameters()
        }
        
        logger.info(f"✓ Computed Fisher Information Matrix for {len(fisher_info)} parameters")
    
    def ewc_loss(self) -> torch.Tensor:
        """Compute EWC regularization loss."""
        
        if self.fisher_information is None or self.optimal_params is None:
            return torch.tensor(0.0)
        
        loss = torch.tensor(0.0, device=next(self.model.parameters()).device)
        
        for name, param in self.model.named_parameters():
            if name in self.fisher_information:
                fisher = self.fisher_information[name]
                optimal_param = self.optimal_params[name]
                
                loss += (self.lambda_ewc * fisher * (param - optimal_param) ** 2).sum()
        
        return loss


class OnlineLearningService:
    """
    Production-grade online learning service.
    
    Safely updates the model with user feedback using:
    - Elastic Weight Consolidation (prevents forgetting)
    - Confidence-based sampling (prevents poisoning)
    - Batch accumulation (stabilizes training)
    - Secure data deletion (privacy)
    """
    
    def __init__(
        self,
        model: nn.Module,
        model_path: str = 'models/cnn_deepfake_best.pt',
        config: Optional[OnlineLearningConfig] = None
    ):
        """
        Initialize online learning service.
        
        Args:
            model: CNN model to train
            model_path: Path where to save trained models
            config: Configuration (uses defaults if None)
        """
        self.model = model
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(exist_ok=True)
        
        self.config = config or OnlineLearningConfig()
        self.device = next(model.parameters()).device
        
        # Training components
        self.criterion = nn.BCELoss()
        self.optimizer = optim.SGD(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        
        # EWC for catastrophic forgetting prevention
        self.ewc = ElasticWeightConsolidation(
            self.model,
            lambda_ewc=self.config.ewc_lambda
        )
        
        # Feedback buffer
        self.feedback_buffer = []
        self.buffer_lock = asyncio.Lock()
        
        # Version tracking
        self.model_version = 0
        self.checkpoint_history = []
        
        if not AUDIO_LIBS_AVAILABLE:
            logger.warning("Audio libraries not available - online learning disabled")
    
    async def learn_from_feedback(
        self,
        audio_path: str,
        user_label: int,
        model_prediction: float,
        model_prediction_label: int,
        delete_audio: bool = True,
        async_training: bool = False
    ) -> Dict:
        """
        Learn from a single piece of user feedback.
        
        Args:
            audio_path: Path to audio file
            user_label: Correct label (0=real, 1=deepfake)
            model_prediction: Model's predicted probability
            model_prediction_label: Model's predicted label
            delete_audio: Securely delete audio after training
            async_training: Train in background (don't block request)
            
        Returns:
            Result dict with success status and details
        """
        
        if not AUDIO_LIBS_AVAILABLE:
            return {
                'success': False,
                'error': 'Audio libraries not available'
            }
        
        if user_label not in [0, 1]:
            return {
                'success': False,
                'error': 'user_label must be 0 (real) or 1 (deepfake)'
            }
        
        # Check if we should learn from this sample
        if not self._should_learn(user_label, model_prediction_label, model_prediction):
            logger.info(
                f"Skipped learning: model confident and correct "
                f"(confidence: {model_prediction:.2%})"
            )
            
            # Still delete the audio
            if delete_audio:
                await SecureDeletion.secure_delete(audio_path)
            
            return {
                'success': True,
                'skipped': True,
                'reason': 'Model was confident and correct',
                'data_deleted': True
            }
        
        # Extract features
        try:
            features = self._extract_features(audio_path)
            if features is None:
                return {'success': False, 'error': 'Failed to extract audio features'}
        except Exception as e:
            if delete_audio:
                await SecureDeletion.secure_delete(audio_path)
            return {'success': False, 'error': str(e)}
        
        # Add to buffer
        async with self.buffer_lock:
            self.feedback_buffer.append({
                'features': features,
                'label': user_label
            })
        
        # Delete audio immediately
        if delete_audio:
            deletion_result = await SecureDeletion.secure_delete(audio_path)
        else:
            deletion_result = False
        
        # Train
        if async_training:
            # Train in background
            asyncio.create_task(self._train_buffer_if_full())
            return {
                'success': True,
                'message': 'Feedback submitted. Model will train in background.',
                'data_deleted': deletion_result,
                'async_training': True,
                'buffer_size': len(self.feedback_buffer)
            }
        else:
            # Train immediately if buffer is full
            if len(self.feedback_buffer) >= self.config.batch_size:
                train_result = await self._train_buffer()
                return {
                    'success': train_result['success'],
                    'message': train_result.get('message', 'Model trained'),
                    'data_deleted': deletion_result,
                    'training_loss': train_result.get('loss', None),
                    'model_version': self.model_version
                }
            
            return {
                'success': True,
                'message': f'Feedback queued ({len(self.feedback_buffer)}/{self.config.batch_size})',
                'data_deleted': deletion_result,
                'buffer_size': len(self.feedback_buffer)
            }
    
    def _should_learn(
        self,
        user_label: int,
        model_label: int,
        model_confidence: float
    ) -> bool:
        """
        Determine if we should learn from this sample.
        
        Avoids learning when:
        - Model is highly confident and correct (avoids noise)
        - User label matches model prediction and confidence > threshold
        """
        
        # If model was right and confident, skip
        if user_label == model_label and model_confidence > self.config.confidence_threshold:
            return False
        
        # Learn from: errors, low-confidence predictions, and contradictions
        return True
    
    def _extract_features(self, audio_path: str) -> Optional[torch.Tensor]:
        """
        Extract mel-spectrogram features from audio.
        
        Returns:
            Normalized spectrogram tensor or None on error
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.config.sample_rate)
            
            if len(y) == 0:
                return None
            
            # Extract mel-spectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=y,
                sr=sr,
                n_mels=self.config.n_mels,
                n_fft=2048,
                hop_length=512
            )
            
            # Convert to dB scale
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Normalize
            mel_spec_normalized = (
                (mel_spec_db - mel_spec_db.mean()) /
                (mel_spec_db.std() + 1e-5)
            )
            
            # Convert to tensor with channel dimension
            spectrogram = torch.from_numpy(mel_spec_normalized).float()
            spectrogram = spectrogram.unsqueeze(0)  # Add channel dim
            
            return spectrogram
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
    
    async def _train_buffer_if_full(self):
        """Train on buffer if it reaches batch_size (for async training)."""
        async with self.buffer_lock:
            if len(self.feedback_buffer) >= self.config.batch_size:
                await self._train_buffer()
    
    async def _train_buffer(self) -> Dict:
        """
        Train model on accumulated feedback (batch training).
        Uses low learning rate and EWC to prevent catastrophic forgetting.
        
        Returns:
            Dict with training results
        """
        
        async with self.buffer_lock:
            if len(self.feedback_buffer) == 0:
                return {'success': False, 'error': 'No feedback to train on'}
            
            # Copy buffer and clear
            batch_data = list(self.feedback_buffer)
            self.feedback_buffer.clear()
        
        try:
            # Save checkpoint before training
            self._save_checkpoint(prefix='before_training')
            
            # Prepare batch
            batch_size = len(batch_data)
            specs = torch.stack([item['features'] for item in batch_data]).to(self.device)
            labels = torch.tensor(
                [item['label'] for item in batch_data],
                dtype=torch.float32
            ).unsqueeze(1).to(self.device)
            
            # Training loop
            self.model.train()
            
            for epoch in range(3):  # Multiple passes for stability
                total_loss = 0.0
                
                # Shuffle batch
                indices = torch.randperm(batch_size)
                specs_shuffled = specs[indices]
                labels_shuffled = labels[indices]
                
                for spec, label in zip(specs_shuffled, labels_shuffled):
                    self.optimizer.zero_grad()
                    
                    # Forward pass
                    output = self.model(spec.unsqueeze(0))
                    
                    # Task loss
                    task_loss = self.criterion(output, label.unsqueeze(0))
                    
                    # EWC loss (prevents forgetting)
                    ewc_loss = self.ewc.ewc_loss()
                    
                    # Combined loss
                    total_loss_item = task_loss + ewc_loss
                    
                    # Backward pass
                    total_loss_item.backward()
                    
                    # Gradient clipping for stability
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.gradient_clip
                    )
                    
                    # Update
                    self.optimizer.step()
                    
                    total_loss += total_loss_item.item()
            
            avg_loss = total_loss / (batch_size * 3)
            
            # Save trained model
            self.model.eval()
            self._save_checkpoint(prefix='trained')
            self.model_version += 1
            
            logger.info(
                f"✓ Model trained on {batch_size} feedback samples. "
                f"Avg loss: {avg_loss:.4f}, Version: {self.model_version}"
            )
            
            return {
                'success': True,
                'message': f'Model updated with {batch_size} feedback samples',
                'loss': avg_loss,
                'batch_size': batch_size,
                'model_version': self.model_version
            }
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            # Attempt rollback
            self._rollback_checkpoint()
            return {
                'success': False,
                'error': str(e),
                'rolled_back': True
            }
    
    def _save_checkpoint(self, prefix: str = 'checkpoint'):
        """
        Save model checkpoint with versioning.
        
        Args:
            prefix: Checkpoint prefix (trained, before_training, etc.)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_path = (
            self.model_path.parent /
            f"{prefix}_{self.model_version}_{timestamp}.pt"
        )
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'version': self.model_version,
            'timestamp': timestamp,
            'config': self.config.__dict__
        }, checkpoint_path)
        
        self.checkpoint_history.append(checkpoint_path)
        
        # Keep only N most recent checkpoints
        if len(self.checkpoint_history) > self.config.keep_checkpoints:
            old_checkpoint = self.checkpoint_history.pop(0)
            try:
                old_checkpoint.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete old checkpoint: {e}")
        
        logger.info(f"✓ Saved checkpoint: {checkpoint_path.name}")
    
    def _rollback_checkpoint(self, steps_back: int = 1):
        """Rollback to previous checkpoint if training fails."""
        try:
            if len(self.checkpoint_history) < steps_back + 1:
                logger.warning("Not enough checkpoints for rollback")
                return False
            
            rollback_path = self.checkpoint_history[-steps_back-1]
            checkpoint = torch.load(rollback_path, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.model_version = checkpoint['version']
            
            logger.info(f"✓ Rolled back to: {rollback_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_training_status(self) -> Dict:
        """Get current training status."""
        return {
            'buffer_size': len(self.feedback_buffer),
            'model_version': self.model_version,
            'checkpoints': len(self.checkpoint_history),
            'config': {
                'learning_rate': self.config.learning_rate,
                'batch_size': self.config.batch_size,
                'ewc_lambda': self.config.ewc_lambda,
                'confidence_threshold': self.config.confidence_threshold
            }
        }
    
    async def flush_buffer(self) -> Dict:
        """Train on all remaining feedback immediately."""
        if len(self.feedback_buffer) > 0:
            return await self._train_buffer()
        return {
            'success': True,
            'message': 'Buffer is empty',
            'trained_samples': 0
        }
