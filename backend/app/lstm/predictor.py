import os
import numpy as np
import logging
from app.core.config import settings
from app.lstm.model import build_lstm_model

os.environ.setdefault("KERAS_BACKEND", "torch")

try:
    import keras_core as keras
except ImportError:
    try:
        import keras
    except ImportError:
        keras = None

logger = logging.getLogger("railmind")

class LSTMPredictor:
    def __init__(self):
        self.models = {}
        self.load_behavior_models()

    def _create_default_model(self, model_file_path: str, sequence_length: int = 30, num_features: int = 34):
        os.makedirs(os.path.dirname(model_file_path), exist_ok=True)
        model = build_lstm_model(sequence_length=sequence_length, num_features=num_features)
        model.save(model_file_path, save_format="h5")
        logger.warning("Created default LSTM model at '%s'", model_file_path)
        return model

    def load_behavior_models(self):
        """Pre-loads saved .h5 network frameworks into memory."""
        if not keras:
            raise RuntimeError("Keras is required for LSTM inference but is not installed.")

        target_blueprints = {
            "suicide": "suicide_classifier.h5",
            "pickpocket": "pickpocket_classifier.h5",
            "anomaly": "anomaly_classifier.h5"
        }

        for classification_key, file_name in target_blueprints.items():
            model_file_path = os.path.join(settings.MODEL_DIR, file_name)

            if not os.path.exists(model_file_path):
                logger.warning(
                    "Missing LSTM model for '%s' at '%s'. Generating default model to avoid startup failure.",
                    classification_key,
                    model_file_path,
                )
                self._create_default_model(model_file_path)

            try:
                # compile=False allows running inference workflows without loading training states
                self.models[classification_key] = keras.models.load_model(model_file_path, compile=False)
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