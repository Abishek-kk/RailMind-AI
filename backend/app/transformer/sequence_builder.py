"""Build temporal feature sequences for Transformer behavior input."""

from collections import deque

import numpy as np

from app.core.config import settings


class SequenceBuilder:
    """Builds per-track temporal feature windows."""

    def __init__(self, sequence_length: int | None = None):
        self.sequence_length = sequence_length or settings.TRANSFORMER_SEQUENCE_LENGTH
        self.sequences = {}

    def add_frame(self, track_id, pose_features):
        if track_id not in self.sequences:
            self.sequences[track_id] = deque(maxlen=self.sequence_length)

        frame_vector = np.asarray(pose_features, dtype=float)
        self.sequences[track_id].append(frame_vector)

    def get_sequence(self, track_id):
        sequence = list(self.sequences.get(track_id, []))
        if not sequence:
            return np.zeros((self.sequence_length, 0), dtype=float)
        sequence_array = np.stack(sequence)
        if len(sequence_array) < self.sequence_length:
            padding = np.zeros((self.sequence_length - len(sequence_array), sequence_array.shape[1]), dtype=float)
            sequence_array = np.vstack([padding, sequence_array])
        return sequence_array

    def is_sequence_complete(self, track_id):
        return len(self.sequences.get(track_id, [])) >= self.sequence_length

    def reset_sequence(self, track_id):
        self.sequences.pop(track_id, None)
