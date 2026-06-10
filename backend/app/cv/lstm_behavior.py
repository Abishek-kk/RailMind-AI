import numpy as np
from typing import Dict, List

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

    def analyze_temporal_sequence(self, track_id: str, feature_vector: List[float]) -> float:
        """
        Adds the current frame's semantic feature vector to the track's sequence,
        and runs inference when a full 30-frame history is available.
        """
        self.sequence_builder.add_frame(track_id, feature_vector)

        if not self.sequence_builder.is_sequence_complete(track_id):
            return 0.0

        sequence_matrix = self.sequence_builder.get_sequence(track_id)
        input_tensor = np.expand_dims(sequence_matrix, axis=0)

        score = self.predictor.run_inference("suicide", input_tensor)
        return round(score, 2)

    def clear_track_history(self, track_id: str):
        """Removes sequence history when a person completely leaves the camera view."""
        self.sequence_builder.reset_sequence(track_id)