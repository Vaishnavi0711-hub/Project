"""
CNN Architecture for Deepfake Detection
Trains on mel-spectrograms to detect synthetic/deepfake speech
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DeepfakeCNN(nn.Module):
    """
    Convolutional Neural Network for deepfake detection.
    
    Input shape: (batch_size, 1, height=128, width=time_steps)
    - 1 channel (mel-spectrogram)
    - 128 mel frequency bins
    - Variable time steps (audio duration)
    
    Output: Probability [0, 1] where 1 = deepfake, 0 = real
    """
    
    def __init__(self, dropout_rate=0.5):
        super(DeepfakeCNN, self).__init__()
        
        # Block 1: Extract low-level frequency patterns
        self.conv1 = nn.Conv2d(1, 32, kernel_size=(3, 3), padding=(1, 1))
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d((2, 2))
        
        # Block 2: Extract mid-level patterns
        self.conv2 = nn.Conv2d(32, 64, kernel_size=(3, 3), padding=(1, 1))
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d((2, 2))
        
        # Block 3: Extract high-level patterns
        self.conv3 = nn.Conv2d(64, 128, kernel_size=(3, 3), padding=(1, 1))
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d((2, 2))
        
        # Block 4: Fine-grained temporal patterns
        self.conv4 = nn.Conv2d(128, 256, kernel_size=(3, 3), padding=(1, 1))
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d((2, 2))
        
        # Global average pooling (works with variable time steps)
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Classification head
        self.fc1 = nn.Linear(256, 128)
        self.dropout1 = nn.Dropout(dropout_rate)
        
        self.fc2 = nn.Linear(128, 64)
        self.dropout2 = nn.Dropout(dropout_rate)
        
        self.fc3 = nn.Linear(64, 1)  # Binary classification
    
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, 1, 128, time_steps)
            
        Returns:
            Probability tensor of shape (batch_size, 1) with sigmoid activation
        """
        
        # Conv Block 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)
        
        # Conv Block 2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)
        
        # Conv Block 3
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        x = self.pool3(x)
        
        # Conv Block 4
        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x)
        x = self.pool4(x)
        
        # Global average pooling (adaptive, handles variable sizes)
        x = self.global_pool(x)
        
        # Flatten for fully connected layers
        x = x.view(x.size(0), -1)  # (batch_size, 256)
        
        # Classification layers
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout1(x)
        
        x = self.fc2(x)
        x = F.relu(x)
        x = self.dropout2(x)
        
        x = self.fc3(x)
        x = torch.sigmoid(x)  # Sigmoid for binary classification [0, 1]
        
        return x


class LightweightDeepfakeCNN(nn.Module):
    """
    Lightweight version for faster inference.
    ~5x smaller than DeepfakeCNN
    """
    
    def __init__(self, dropout_rate=0.3):
        super(LightweightDeepfakeCNN, self).__init__()
        
        self.conv1 = nn.Conv2d(1, 16, kernel_size=(3, 3), padding=(1, 1))
        self.bn1 = nn.BatchNorm2d(16)
        self.pool1 = nn.MaxPool2d((2, 2))
        
        self.conv2 = nn.Conv2d(16, 32, kernel_size=(3, 3), padding=(1, 1))
        self.bn2 = nn.BatchNorm2d(32)
        self.pool2 = nn.MaxPool2d((2, 2))
        
        self.conv3 = nn.Conv2d(32, 64, kernel_size=(3, 3), padding=(1, 1))
        self.bn3 = nn.BatchNorm2d(64)
        self.pool3 = nn.MaxPool2d((2, 2))
        
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        self.fc1 = nn.Linear(64, 32)
        self.dropout = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(32, 1)
    
    def forward(self, x):
        """Forward pass through lightweight network."""
        
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)
        
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)
        
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        x = self.pool3(x)
        
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.fc2(x)
        x = torch.sigmoid(x)
        
        return x
