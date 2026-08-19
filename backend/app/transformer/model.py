from __future__ import annotations

import torch
from torch import nn


class TemporalTransformer(nn.Module):
    """Temporal transformer for behaviour-window classification.

    Input shape: (batch_size, sequence_length=30, n_features=7)
    Output shape: (batch_size, n_classes=4)

    The model projects each timestep independently, adds learned positional
    embeddings, passes the sequence through a small transformer encoder, and
    mean-pools across time before the classification head.
    """

    def __init__(
        self,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
        seq_len: int = 30,
        n_features: int = 7,
        n_classes: int = 4,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        self.dim_feedforward = dim_feedforward
        self.dropout = dropout
        self.seq_len = seq_len
        self.n_features = n_features
        self.n_classes = n_classes

        self.input_projection = nn.Linear(n_features, d_model)
        self.position_embedding = nn.Parameter(torch.zeros(seq_len, d_model))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="relu",
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the temporal transformer to a feature window.

        Args:
            x: Tensor of shape (batch, 30, 7).

        Returns:
            Logits with shape (batch, 4).
        """
        if x.dim() != 3:
            raise ValueError(f"Expected input of shape (batch, seq_len, n_features), got {tuple(x.shape)}")
        projected = self.input_projection(x)
        positional = self.position_embedding.unsqueeze(0)
        encoded = projected + positional
        encoded = self.encoder(encoded)
        pooled = encoded.mean(dim=1)
        logits = self.classifier(pooled)
        return logits

    def get_attention_weights(self, x: torch.Tensor) -> torch.Tensor:
        """Return the self-attention weights from the final encoder layer.

        This is useful for debugging which timesteps in the 30-second window most
        strongly influenced the model decision. The returned tensor has shape
        (batch, num_heads, seq_len, seq_len).
        """
        if x.dim() != 3:
            raise ValueError(f"Expected input of shape (batch, seq_len, n_features), got {tuple(x.shape)}")

        projected = self.input_projection(x)
        encoded = projected + self.position_embedding.unsqueeze(0)
        attention_weights = self.encoder.layers[-1].self_attn(
            encoded,
            encoded,
            encoded,
            need_weights=True,
            average_attn_weights=False,
        )[1]
        return attention_weights
