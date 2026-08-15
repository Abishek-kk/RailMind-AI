from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch

from .dataset import CLASS_NAMES, FEATURE_KEYS, LABEL_MAP
from .model import TemporalTransformer


def load_model(checkpoint_path: str | Path, scaler_path: str | Path) -> tuple[TemporalTransformer, Any]:
    """Load a trained transformer checkpoint and the saved StandardScaler."""
    checkpoint = Path(checkpoint_path)
    scaler = joblib.load(Path(scaler_path))

    model = TemporalTransformer()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    state_dict = torch.load(str(checkpoint), map_location=device)
    if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
        state_dict = state_dict["model_state_dict"]
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model, scaler


def predict(
    model: TemporalTransformer,
    scaler: Any,
    feature_sequence: list[dict[str, float]],
) -> dict[str, Any]:
    """Predict a railway behaviour class for a single 30-second feature window.

    Args:
        model: Trained TemporalTransformer.
        scaler: Fitted sklearn StandardScaler.
        feature_sequence: List of 30 dictionaries, each with exactly the seven
            feature keys in the fixed order used during training.

    Returns:
        Dictionary with the predicted class, confidence score, and per-class
        probabilities. The output shape matches the API contract expected by
        the FastAPI backend.
    """
    if len(feature_sequence) != 30:
        raise ValueError(f"Expected exactly 30 timesteps, got {len(feature_sequence)}.")

    if isinstance(feature_sequence, np.ndarray):
        sequence_array = feature_sequence.astype(np.float32, copy=False)
    elif isinstance(feature_sequence, torch.Tensor):
        sequence_array = feature_sequence.detach().cpu().numpy().astype(np.float32, copy=False)
    else:
        sequence_array = np.zeros((30, 7), dtype=np.float32)
        for timestep_index, feature_entry in enumerate(feature_sequence):
            if isinstance(feature_entry, dict):
                for feature_index, key in enumerate(FEATURE_KEYS):
                    sequence_array[timestep_index, feature_index] = float(feature_entry[key])
            else:
                sequence_array[timestep_index] = np.asarray(feature_entry, dtype=np.float32)

    if sequence_array.shape != (30, 7):
        raise ValueError(f"Expected a 30x7 feature window, got shape {tuple(sequence_array.shape)}.")

    scaled = scaler.transform(sequence_array.reshape(-1, 7)).reshape(30, 7)
    tensor = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)

    device = next(model.parameters()).device
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=-1).squeeze(0)

    predicted_index = int(torch.argmax(probabilities).item())
    predicted_class = CLASS_NAMES[predicted_index]
    confidence = float(probabilities[predicted_index].item())

    probability_map: dict[str, float] = {
        label: float(probabilities[index].item()) for index, label in enumerate(CLASS_NAMES)
    }

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": probability_map,
    }
