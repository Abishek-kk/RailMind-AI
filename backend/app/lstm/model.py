import torch
import torch.nn as nn

from app.core.config import settings


class LSTMBehaviorModel(nn.Module):
    """
    Stacked LSTM neural network for temporal skeletal sequence classification.
    Input Shape: (Batch_Size, Sequence_Length, Num_Features) -> e.g., (32, 30, 7)
    """

    def __init__(self, sequence_length: int = 30, num_features: int = 7, num_classes: int = 1):
        super().__init__()
        self.sequence_length = sequence_length
        self.num_features = num_features
        self.num_classes = num_classes

        # Layer 1: Processes individual frame vectors sequentially, maintaining sequence memory
        self.lstm1 = nn.LSTM(num_features, 64, batch_first=True, bidirectional=True)
        self.dropout1 = nn.Dropout(0.2)

        # Layer 2: Condenses temporal outputs into a single aggregated feature vector
        self.lstm2 = nn.LSTM(64 * 2, 32, batch_first=True, bidirectional=True)
        self.dropout2 = nn.Dropout(0.2)

        # Dense Layer Context Mapping
        self.fc1 = nn.Linear(32 * 2, 16)
        self.relu = nn.ReLU()

        # Classification Output Layer (Sigmoid output boundary for binary anomaly risk probabilities)
        self.fc2 = nn.Linear(16, num_classes)
        self.activation = nn.Sigmoid() if num_classes == 1 else nn.Softmax(dim=1)

    def forward(self, x):
        """
        Args:
            x: Input tensor of shape (batch_size, sequence_length, num_features)
        Returns:
            Output tensor of shape (batch_size, num_classes)
        """
        # LSTM Layer 1
        x, _ = self.lstm1(x)
        x = self.dropout1(x)

        # LSTM Layer 2
        x, _ = self.lstm2(x)
        x = x[:, -1, :]
        x = self.dropout2(x)

        # Dense layers
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.activation(x)

        return x


def build_lstm_model(sequence_length: int = 30, num_features: int = 7, num_classes: int = 1) -> LSTMBehaviorModel:
    """
    Factory function to build and return an LSTM model.
    """
    return LSTMBehaviorModel(sequence_length, num_features, num_classes)