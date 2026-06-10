"""Detect suspicious following or stalking behavior"""

import math

class FollowingDetector:
    """Detects suspicious following or stalking patterns"""
    
    def __init__(self, distance_threshold=2.0):
        """Initialize with distance threshold"""
        self.distance_threshold = distance_threshold
    
    def detect(self, tracks):
        """Detect following patterns between tracked people"""
        suspicious = []
        track_ids = list(tracks.keys())
        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                first = tracks[track_ids[i]]
                second = tracks[track_ids[j]]
                distance = self.calculate_distance_between_tracks(first, second)
                similarity = self.analyze_trajectory_similarity(first, second)
                if distance is not None and distance <= self.distance_threshold and similarity >= 0.6:
                    suspicious.append({
                        "track_1": track_ids[i],
                        "track_2": track_ids[j],
                        "distance": distance,
                        "similarity": similarity,
                    })
        return suspicious

    def get_following_distance(self, track_id, tracks):
        """Return the minimum distance from this track to any other active track."""
        if track_id not in tracks:
            return float('inf')
        distances = []
        for other_id, other_data in tracks.items():
            if other_id == track_id:
                continue
            distance = self.calculate_distance_between_tracks(tracks[track_id], other_data)
            if distance is not None:
                distances.append(distance)
        return float(min(distances)) if distances else float('inf')

    def get_crowd_interaction_count(self, track_id, tracks):
        """Count nearby tracks that may indicate crowd interaction."""
        if track_id not in tracks:
            return 0
        count = 0
        for other_id, other_data in tracks.items():
            if other_id == track_id:
                continue
            distance = self.calculate_distance_between_tracks(tracks[track_id], other_data)
            if distance is not None and distance <= self.distance_threshold * 10:
                count += 1
        return count

    def analyze_trajectory_similarity(self, track1, track2):
        """Analyze if two tracks follow similar paths"""
        trajectory1 = track1.get("trajectory") or []
        trajectory2 = track2.get("trajectory") or []
        if not trajectory1 or not trajectory2:
            return 0.0
        common_length = min(len(trajectory1), len(trajectory2))
        if common_length == 0:
            return 0.0
        matches = 0
        for a, b in zip(trajectory1[-common_length:], trajectory2[-common_length:]):
            if math.dist(a, b) < self.distance_threshold * 10:
                matches += 1
        return matches / common_length
    
    def calculate_distance_between_tracks(self, track1, track2):
        """Calculate distance between two tracked persons"""
        p1 = track1.get("center") or track1.get("position")
        p2 = track2.get("center") or track2.get("position")
        if p1 is None or p2 is None:
            return None
        return math.dist(p1, p2)
