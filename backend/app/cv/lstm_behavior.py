import numpy as np
import logging
from typing import List

from app.core.config import settings
from app.lstm.predictor import LSTMPredictor
from app.lstm.sequence_builder import SequenceBuilder

logger = logging.getLogger("railmind")

class BehaviorAnalyzer:
    def __init__(self, window_size: int | None = None):
        """
        Sets up sequence building and inference for behavior classification.
        """
        self.window_size = window_size or settings.LSTM_SEQUENCE_LENGTH
        self.sequence_builder = SequenceBuilder(sequence_length=self.window_size)
        self.predictor = LSTMPredictor()
        self.model_targets = ("suicide", "pickpocket", "anomaly")
        self.models_available = all(self.predictor.has_model(target) for target in self.model_targets)
        if not self.models_available:
            logger.error(
                "LSTM behavior analysis disabled because trained model weights are missing: %s",
                sorted(self.predictor.unavailable_models),
            )

    def analyze_temporal_sequence(self, track_id: str, feature_vector: List[float]) -> dict[str, float]:
        """
        Adds the current frame's semantic feature vector to the track's sequence,
        and runs inference when a full 30-frame history is available.
        """
        self.sequence_builder.add_frame(track_id, feature_vector)

        if not self.sequence_builder.is_sequence_complete(track_id):
            return {"suicide": 0.0, "pickpocket": 0.0, "anomaly": 0.0}

        if not self.models_available:
            return {"suicide": 0.0, "pickpocket": 0.0, "anomaly": 0.0}

        sequence_matrix = self.sequence_builder.get_sequence(track_id)
        input_tensor = np.expand_dims(sequence_matrix, axis=0)

        scores = {
            "suicide": round(self.predictor.run_inference("suicide", input_tensor), 2),
            "pickpocket": round(self.predictor.run_inference("pickpocket", input_tensor), 2),
            "anomaly": round(self.predictor.run_inference("anomaly", input_tensor), 2),
        }
        return scores

    def clear_track_history(self, track_id: str):
        """Removes sequence history when a person completely leaves the camera view."""
        self.sequence_builder.reset_sequence(track_id)

    def determine_behavior_label(
        self,
        scores: dict[str, float],
        following_distance: float | None = None,
    ) -> str:
        """Translate LSTM model scores into dashboard pose classification labels."""
        suicide_score = scores.get("suicide", 0.0)
        pickpocket_score = scores.get("pickpocket", 0.0)
        anomaly_score = scores.get("anomaly", 0.0)
        high_score_threshold = settings.BEHAVIOR_HIGH_SCORE_THRESHOLD
        erratic_score_threshold = settings.BEHAVIOR_ERRATIC_SCORE_THRESHOLD
        following_distance_threshold = settings.BEHAVIOR_FOLLOWING_DISTANCE_METERS

        if suicide_score >= high_score_threshold:
            return "distress"
        if (
            pickpocket_score >= high_score_threshold
            and following_distance is not None
            and following_distance < following_distance_threshold
        ):
            return "following"
        if pickpocket_score >= high_score_threshold:
            return "suspicious"
        if anomaly_score >= high_score_threshold:
            return "suspicious"
        if max(suicide_score, pickpocket_score, anomaly_score) >= erratic_score_threshold:
            return "erratic"
        return "normal"
