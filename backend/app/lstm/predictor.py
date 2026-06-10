import os
import logging
import pickle
from typing import Set

import numpy as np
import torch

from app.core.config import settings
from app.lstm.model import build_lstm_model

logger = logging.getLogger("railmind")


class LSTMPredictor:
    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}
        self.scalers = {}
        self.unavailable_models: Set[str] = set()
        self._warned_unavailable: Set[str] = set()
        self.load_behavior_models()
        logger.info(f"LSTMPredictor using device: {self.device}")

    def load_behavior_models(self):
        """Pre-loads saved .pt model weights and feature scalers into memory."""
        target_blueprints = {
            "suicide": "suicide_classifier.pt",
            "pickpocket": "pickpocket_classifier.pt",
            "anomaly": "anomaly_classifier.pt",
        }

        for classification_key, file_name in target_blueprints.items():
            model_file_path = os.path.join(settings.MODEL_DIR, file_name)
            scaler_file_path = model_file_path.replace(".pt", "_scaler.pkl")

            if not os.path.exists(model_file_path):
                self.unavailable_models.add(classification_key)
                logger.error(
                    "Missing trained LSTM model for '%s' at '%s'. "
                    "Inference for this target will return 0.0 until trained weights are provided.",
                    classification_key,
                    model_file_path,
                )
                self.scalers[classification_key] = None
            else:
                try:
                    # Load model weights
                    model = build_lstm_model(
                        sequence_length=settings.LSTM_SEQUENCE_LENGTH,
                        num_features=settings.LSTM_FEATURE_COUNT,
                    )
                    model.load_state_dict(torch.load(model_file_path, map_location=self.device))
                    model.to(self.device)
                    model.eval()  # Set to evaluation mode
                    self.models[classification_key] = model
                    logger.info(f"Initialized PyTorch Model: {file_name}")
                    
                    # Load feature scaler if available
                    scaler = None
                    if os.path.exists(scaler_file_path):
                        with open(scaler_file_path, "rb") as f:
                            scaler = pickle.load(f)
                        logger.info(f"Loaded feature scaler for {classification_key}")
                    else:
                        logger.warning(f"Feature scaler not found for {classification_key} at {scaler_file_path}")
                    
                    self.scalers[classification_key] = scaler
                except Exception as err:
                    raise RuntimeError(f"Failed to load LSTM model '{file_name}': {err}") from err

    def has_model(self, model_target: str) -> bool:
        return model_target in self.models

    def run_inference(self, model_target: str, input_tensor: np.ndarray) -> float:
        """Runs the prepared input matrix block down target network tracks."""
        if model_target not in self.models:
            if model_target not in self._warned_unavailable:
                logger.warning(
                    "Skipping LSTM inference for unavailable target '%s'. Returning neutral score 0.0.",
                    model_target,
                )
                self._warned_unavailable.add(model_target)
            return 0.0

        try:
            # Apply feature scaling if scaler is available
            scaled_input = input_tensor.copy()
            scaler = self.scalers.get(model_target)
            if scaler is not None:
                # Reshape for scaler application
                orig_shape = scaled_input.shape
                scaled_input = scaled_input.reshape(-1, orig_shape[-1])
                scaled_input = scaler.transform(scaled_input)
                scaled_input = scaled_input.reshape(orig_shape)
            
            # Convert numpy array to torch tensor
            input_torch = torch.tensor(scaled_input, dtype=torch.float32).to(self.device)

            # Add batch dimension if necessary
            if len(input_torch.shape) == 2:
                input_torch = input_torch.unsqueeze(0)

            # Run inference
            with torch.no_grad():
                model = self.models[model_target]
                output = model(input_torch)

            return float(output[0][0].cpu().numpy())
        except Exception as inference_err:
            raise RuntimeError(
                f"LSTM inference failure for target '{model_target}': {inference_err}"
            ) from inference_err
