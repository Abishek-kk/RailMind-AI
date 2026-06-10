import os
import logging

import numpy as np
import torch

from app.core.config import settings
from app.lstm.model import build_lstm_model

logger = logging.getLogger("railmind")


class LSTMPredictor:
    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}
        self.load_behavior_models()
        logger.info(f"LSTMPredictor using device: {self.device}")

    def _create_default_model(self, model_file_path: str, sequence_length: int = 30, num_features: int = 34):
        """Creates and saves a default model if one doesn't exist."""
        os.makedirs(os.path.dirname(model_file_path), exist_ok=True)
        model = build_lstm_model(sequence_length=sequence_length, num_features=num_features)
        torch.save(model.state_dict(), model_file_path)
        logger.warning("Created default LSTM model at '%s'", model_file_path)
        return model

    def load_behavior_models(self):
        """Pre-loads saved .pt model weights into memory."""
        target_blueprints = {
            "suicide": "suicide_classifier.pt",
            "pickpocket": "pickpocket_classifier.pt",
            "anomaly": "anomaly_classifier.pt",
        }

        for classification_key, file_name in target_blueprints.items():
            model_file_path = os.path.join(settings.MODEL_DIR, file_name)

            if not os.path.exists(model_file_path):
                logger.warning(
                    "Missing LSTM model for '%s' at '%s'. Generating default model to avoid startup failure.",
                    classification_key,
                    model_file_path,
                )
                model = self._create_default_model(model_file_path)
                self.models[classification_key] = model.to(self.device)
            else:
                try:
                    # Load model weights
                    model = build_lstm_model()
                    model.load_state_dict(torch.load(model_file_path, map_location=self.device))
                    model.to(self.device)
                    model.eval()  # Set to evaluation mode
                    self.models[classification_key] = model
                    logger.info(f"Initialized PyTorch Model: {file_name}")
                except Exception as err:
                    raise RuntimeError(f"Failed to load LSTM model '{file_name}': {err}") from err

    def run_inference(self, model_target: str, input_tensor: np.ndarray) -> float:
        """Runs the prepared input matrix block down target network tracks."""
        if model_target not in self.models:
            raise RuntimeError(
                f"Requested LSTM model '{model_target}' is not loaded. Loaded models: {list(self.models.keys())}."
            )

        try:
            # Convert numpy array to torch tensor
            input_torch = torch.tensor(input_tensor, dtype=torch.float32).to(self.device)

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