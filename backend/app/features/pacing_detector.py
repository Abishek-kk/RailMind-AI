"""Detect pacing behavior (repetitive walking patterns)"""

import numpy as np

class PacingDetector:
    """Detects pacing or repetitive walking patterns"""
    
    def __init__(self, window_size=30):
        """Initialize with time window"""
        self.window_size = window_size
        self.position_history = {}
        self.pacing_counts = {}
    
    def detect(self, track_id, pose):
        """Detect pacing for a tracked person"""
        if track_id not in self.position_history:
            self.position_history[track_id] = []
            self.pacing_counts[track_id] = 0
        center = pose.get("center") or pose.get("position")
        if center is None:
            return 0
        self.position_history[track_id].append(center)
        if len(self.position_history[track_id]) > self.window_size:
            self.position_history[track_id].pop(0)
        if len(self.position_history[track_id]) < self.window_size:
            return 0
        variance = self.calculate_path_variance(self.position_history[track_id])
        if variance < 100.0:
            self.pacing_counts[track_id] += 1
            return self.pacing_counts[track_id]
        return 0
    
    def calculate_path_variance(self, positions):
        """Calculate variance in movement path"""
        if not positions:
            return 0.0
        arr = np.asarray(positions, dtype=float)
        return float(np.var(arr, axis=0).sum())
