import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Sinusoidal temporal position encoding for fixed-length feature sequences."""

    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        position = torch.arange(max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model))

        pe = torch.zeros(max_len, d_model, dtype=torch.float32)
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 == 1:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
            pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class TemporalTransformerBehaviorModel(nn.Module):
    """
    Transformer encoder classifier for RailMind temporal behavior features.

    Input shape: (batch, sequence_length, num_features), e.g. (B, 30, 7).
    This is a TimeSformer-style temporal attention model for feature sequences:
    per-frame behavior vectors are projected to tokens, temporal self-attention
    models the 30-frame history, and a pooled token classifies behavior.
    """

    def __init__(
        self,
        sequence_length: int = 30,
        num_features: int = 7,
        num_classes: int = 4,
        d_model: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        if num_classes < 2:
            raise ValueError("TemporalTransformerBehaviorModel requires at least 2 classes")
        if d_model % num_heads != 0:
            raise ValueError("d_model must be divisible by num_heads")

        self.sequence_length = sequence_length
        self.num_features = num_features
        self.num_classes = num_classes

        self.input_projection = nn.Linear(num_features, d_model)
        self.positional_encoding = PositionalEncoding(d_model, max_len=sequence_length)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, num_classes),
        )
        self.activation = nn.Softmax(dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_projection(x)
        x = self.positional_encoding(x)
        x = self.encoder(x)
        x = self.norm(x)
        pooled = x.mean(dim=1)
        logits = self.classifier(pooled)
        return self.activation(logits)


def build_temporal_transformer_model(
    sequence_length: int = 30,
    num_features: int = 7,
    num_classes: int = 4,
) -> TemporalTransformerBehaviorModel:
    return TemporalTransformerBehaviorModel(sequence_length, num_features, num_classes)
