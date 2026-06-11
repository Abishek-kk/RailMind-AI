"""Detect loitering behavior (staying in one area for too long)"""

from collections import deque

import numpy as np

class LoiteringDetector:
    """Detects loitering behavior"""
    
    def __init__(self, duration_threshold=60, fps=30):
        """Initialize with duration threshold in seconds"""
        self.duration_threshold = duration_threshold
        self.fps = fps
        self.max_history = max(1, int(duration_threshold * fps))
        self.presence_tracking = {}
        self.first_seen_frames = {}
    
    def detect(self, track_id, pose, frame_id):
        """Detect loitering for tracked person"""
        if track_id not in self.presence_tracking:
            self.presence_tracking[track_id] = deque(maxlen=self.max_history)
            self.first_seen_frames[track_id] = frame_id
        center = pose.get("center") or pose.get("position")
        if center is None:
            return 0.0
        self.presence_tracking[track_id].append(center)
        duration_seconds = max(0.0, (frame_id - self.first_seen_frames.get(track_id, frame_id)) / self.fps)
        movement_range = self.calculate_movement_range(self.presence_tracking[track_id])
        if duration_seconds >= self.duration_threshold and movement_range < 100.0:
            return float(duration_seconds)
        return 0.0
    
    def calculate_movement_range(self, positions):
        """Calculate area covered by person"""
        if not positions:
            return 0.0
        arr = np.asarray(positions, dtype=float)
        min_xy = np.min(arr, axis=0)
        max_xy = np.max(arr, axis=0)
        return float(np.linalg.norm(max_xy - min_xy))

    def clear_track(self, track_id):
        """Release stored history for a track that has left the frame."""
        self.presence_tracking.pop(track_id, None)
        self.first_seen_frames.pop(track_id, None)
