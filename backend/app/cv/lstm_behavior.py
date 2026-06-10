import numpy as np
from typing import List

from app.lstm.predictor import LSTMPredictor
from app.lstm.sequence_builder import SequenceBuilder

class BehaviorAnalyzer:
    def __init__(self, window_size: int = 30):
        """
        Sets up sequence building and inference for behavior classification.
        """
        self.window_size = window_size
        self.sequence_builder = SequenceBuilder(sequence_length=window_size)
        self.predictor = LSTMPredictor()

    def analyze_temporal_sequence(self, track_id: str, feature_vector: List[float]) -> dict[str, float]:
        """
        Adds the current frame's semantic feature vector to the track's sequence,
        and runs inference when a full 30-frame history is available.
        """
        self.sequence_builder.add_frame(track_id, feature_vector)

        if not self.sequence_builder.is_sequence_complete(track_id):
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

        if suicide_score > 0.65:
            return "distress"
        if pickpocket_score > 0.65 and following_distance is not None and following_distance < 1.2:
            return "following"
        if pickpocket_score > 0.65:
            return "suspicious"
        if anomaly_score > 0.65:
            return "suspicious"
        if max(suicide_score, pickpocket_score, anomaly_score) > 0.4:
            return "erratic"
        return "normal"