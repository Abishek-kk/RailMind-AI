import logging
import os
import pickle
from typing import Set

import numpy as np
import torch

from app.core.config import settings
from app.transformer.model import build_temporal_transformer_model

logger = logging.getLogger("railmind")


class TemporalTransformerPredictor:
    """Loads the 4-class temporal Transformer and exposes per-risk probabilities."""

    MODEL_FILE_NAME = "behavior_classifier.pt"
    TARGET_CLASS_INDEX = {
        "normal": 0,
        "suicide": 1,
        "pickpocket": 2,
        "anomaly": 3,
    }

    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.scaler = None
        self.models = {}
        self.unavailable_models: Set[str] = set()
        self._warned_unavailable: Set[str] = set()
        self.load_behavior_model()
        logger.info("TemporalTransformerPredictor using device: %s", self.device)

    def load_behavior_model(self):
        model_file_path = os.path.join(settings.MODEL_DIR, self.MODEL_FILE_NAME)
        scaler_file_path = model_file_path.replace(".pt", "_scaler.pkl")

        if not os.path.exists(model_file_path):
            self.unavailable_models = set(self.TARGET_CLASS_INDEX)
            logger.error(
                "Missing trained 4-class temporal Transformer model at '%s'. "
                "Inference will return 0.0 until trained weights are provided.",
                model_file_path,
            )
            return

        try:
            model = build_temporal_transformer_model(
                sequence_length=settings.TRANSFORMER_SEQUENCE_LENGTH,
                num_features=settings.TRANSFORMER_FEATURE_COUNT,
                num_classes=len(self.TARGET_CLASS_INDEX),
            )
            model.load_state_dict(torch.load(model_file_path, map_location=self.device))
            model.to(self.device)
            model.eval()
            self.model = model
            self.models = dict.fromkeys(self.TARGET_CLASS_INDEX, model)

            if os.path.exists(scaler_file_path):
                with open(scaler_file_path, "rb") as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded temporal Transformer feature scaler")
            else:
                logger.warning("Feature scaler not found at %s", scaler_file_path)
        except Exception as err:
            raise RuntimeError(f"Failed to load temporal Transformer model '{self.MODEL_FILE_NAME}': {err}") from err

    def has_model(self, model_target: str) -> bool:
        return self.model is not None and model_target in self.TARGET_CLASS_INDEX

    def run_inference(self, model_target: str, input_tensor: np.ndarray) -> float:
        if not self.has_model(model_target):
            if model_target not in self._warned_unavailable:
                logger.warning(
                    "Skipping temporal Transformer inference for unavailable target '%s'. Returning neutral score 0.0.",
                    model_target,
                )
                self._warned_unavailable.add(model_target)
            return 0.0

        try:
            scaled_input = input_tensor.copy()
            if self.scaler is not None:
                orig_shape = scaled_input.shape
                scaled_input = scaled_input.reshape(-1, orig_shape[-1])
                scaled_input = self.scaler.transform(scaled_input)
                scaled_input = scaled_input.reshape(orig_shape)

            input_torch = torch.tensor(scaled_input, dtype=torch.float32).to(self.device)
            if len(input_torch.shape) == 2:
                input_torch = input_torch.unsqueeze(0)

            with torch.no_grad():
                output = self.model(input_torch)

            class_index = self.TARGET_CLASS_INDEX[model_target]
            return float(output[0][class_index].cpu().numpy())
        except Exception as inference_err:
            raise RuntimeError(
                f"Temporal Transformer inference failure for target '{model_target}': {inference_err}"
            ) from inference_err
