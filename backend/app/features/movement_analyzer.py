"""Analyze movement patterns and anomalies"""

import math

class MovementAnalyzer:
    """Analyzes movement patterns for anomalies"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.movement_history = {}
        self.position_history = {}
    
    def calculate_velocity(self, pose, previous_pose, frame_rate=30):
        """Calculate movement velocity"""
        if pose is None or previous_pose is None:
            return 0.0
        current = pose.get("center") or pose.get("position")
        previous = previous_pose.get("center") or previous_pose.get("position")
        if current is None or previous is None:
            return 0.0
        distance = math.dist(current, previous)
        return distance * frame_rate
    
    def update_track(self, track_id, pose, frame_rate=30):
        """Update movement history and return current speed"""
        if track_id not in self.position_history:
            self.position_history[track_id] = []
        center = pose.get("center") or pose.get("position")
        previous = self.movement_history.get(track_id)
        speed = self.calculate_velocity(pose, previous, frame_rate) if previous is not None else 0.0
        if center is not None:
            self.position_history[track_id].append(center)
            if len(self.position_history[track_id]) > 30:
                self.position_history[track_id].pop(0)
        self.movement_history[track_id] = pose
        return float(speed)

    def get_direction_changes(self, track_id):
        """Analyze frequency of direction changes from recent positions"""
        positions = self.position_history.get(track_id, [])
        if len(positions) < 3:
            return 0
        changes = 0
        for i in range(2, len(positions)):
            prev_vector = (positions[i-1][0] - positions[i-2][0], positions[i-1][1] - positions[i-2][1])
            current_vector = (positions[i][0] - positions[i-1][0], positions[i][1] - positions[i-1][1])
            if prev_vector[0] * current_vector[0] + prev_vector[1] * current_vector[1] < 0:
                changes += 1
        return changes
