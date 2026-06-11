"""Detect pacing behavior (repetitive walking patterns)"""

import numpy as np

class PacingDetector:
    """Detects pacing or repetitive walking patterns"""
    
    def __init__(self, window_size=30, movement_threshold=8.0):
        """Initialize with time window"""
        self.window_size = window_size
        self.movement_threshold = movement_threshold
        self.position_history = {}
    
    def detect(self, track_id, pose):
        """Detect pacing for a tracked person"""
        if track_id not in self.position_history:
            self.position_history[track_id] = []
        center = pose.get("center") or pose.get("position")
        if center is None:
            return 0
        self.position_history[track_id].append(center)
        if len(self.position_history[track_id]) > self.window_size:
            self.position_history[track_id].pop(0)
        if len(self.position_history[track_id]) < self.window_size:
            return 0
        return self.count_direction_reversals(self.position_history[track_id])
    
    def calculate_path_variance(self, positions):
        """Calculate variance in movement path"""
        if not positions:
            return 0.0
        arr = np.asarray(positions, dtype=float)
        return float(np.var(arr, axis=0).sum())

    def count_direction_reversals(self, positions):
        """Count back-and-forth movement cycles within the current window."""
        arr = np.asarray(positions, dtype=float)
        if len(arr) < 3:
            return 0

        x_range = float(np.ptp(arr[:, 0]))
        y_range = float(np.ptp(arr[:, 1]))
        axis_values = arr[:, 0] if x_range >= y_range else arr[:, 1]
        deltas = np.diff(axis_values)

        directions = []
        for delta in deltas:
            if abs(delta) < self.movement_threshold:
                continue
            direction = 1 if delta > 0 else -1
            if not directions or directions[-1] != direction:
                directions.append(direction)

        reversals = max(0, len(directions) - 1)
        return reversals // 2

    def clear_track(self, track_id):
        """Release stored history for a track that has left the frame."""
        self.position_history.pop(track_id, None)
