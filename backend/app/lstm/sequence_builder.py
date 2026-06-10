"""Build sequences from pose data for LSTM input"""

import numpy as np

class SequenceBuilder:
    """Builds temporal sequences from pose keypoints"""
    
    def __init__(self, sequence_length=30):
        """Initialize sequence builder"""
        self.sequence_length = sequence_length
        self.sequences = {}
    
    def add_frame(self, track_id, pose_features):
        """Add frame to sequence for tracked person"""
        if track_id not in self.sequences:
            self.sequences[track_id] = []

        frame_vector = np.asarray(pose_features, dtype=float)
        self.sequences[track_id].append(frame_vector)

        if len(self.sequences[track_id]) > self.sequence_length:
            self.sequences[track_id].pop(0)

        return self.sequences[track_id]
    
    def get_sequence(self, track_id):
        """Get current sequence for person"""
        sequence = self.sequences.get(track_id, [])
        if not sequence:
            return np.zeros((self.sequence_length, 0), dtype=float)
        sequence_array = np.stack(sequence)
        if len(sequence_array) < self.sequence_length:
            padding = np.zeros((self.sequence_length - len(sequence_array), sequence_array.shape[1]), dtype=float)
            sequence_array = np.vstack([padding, sequence_array])
        return sequence_array
    
    def is_sequence_complete(self, track_id):
        """Check if sequence is ready for prediction"""
        return len(self.sequences.get(track_id, [])) >= self.sequence_length
    
    def reset_sequence(self, track_id):
        """Reset sequence for person"""
        self.sequences.pop(track_id, None)
