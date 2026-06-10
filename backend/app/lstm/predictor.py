import os
import numpy as np
import logging
from app.core.config import settings

try:
    import tensorflow as tf
except ImportError:
    tf = None

logger = logging.getLogger("railmind")

class LSTMPredictor:
    def __init__(self):
        self.models = {}
        self.load_behavior_models()

    def load_behavior_models(self):
        """Pre-loads saved .h5 network frameworks into memory."""
        if not tf:
            raise RuntimeError("TensorFlow is required for LSTM inference but is not installed.")

        target_blueprints = {
            "suicide": "suicide_classifier.h5",
            "pickpocket": "pickpocket_classifier.h5",
            "anomaly": "anomaly_classifier.h5"
        }

        for classification_key, file_name in target_blueprints.items():
            model_file_path = os.path.join(settings.MODEL_DIR, file_name)

            if not os.path.exists(model_file_path):
                raise FileNotFoundError(
                    f"Missing LSTM model for '{classification_key}' at '{model_file_path}'. "
                    f"Place '{file_name}' in MODEL_DIR before starting the service."
                )

            try:
                # compile=False allows running inference workflows without loading training states
                self.models[classification_key] = tf.keras.models.load_model(model_file_path, compile=False)
                logger.info(f"Initialized H5 Neural Weight Module: {file_name}")
            except Exception as err:
                raise RuntimeError(f"Failed to load LSTM model '{file_name}': {err}") from err

    def run_inference(self, model_target: str, input_tensor: np.ndarray) -> float:
        """Runs the prepared input matrix block down target network tracks."""
        if model_target in self.models:
            try:
                raw_prediction = self.models[model_target].predict(input_tensor, verbose=0)
                return float(raw_prediction[0][0])
            except Exception as inference_err:
                raise RuntimeError(f"LSTM inference failure for target '{model_target}': {inference_err}") from inference_err

        raise RuntimeError(
            f"Requested LSTM model '{model_target}' is not loaded. Loaded models: {list(self.models.keys())}."
        )