"""Detect when people are too close to platform edges"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from app.core.config import settings


class EdgeProximityDetector:
    """Tracks time spent inside a configured edge safety zone."""

    def __init__(self):
        self.track_in_zone_seconds: Dict[int, float] = defaultdict(float)
        self.track_last_update: Dict[int, datetime] = {}

    def _distance_to_bottom_edge_meters(self, bbox: List[int], frame_height: int) -> Optional[float]:
        if not bbox or len(bbox) < 4:
            return None
        bottom_y = bbox[3]
        pixel_distance = max(frame_height - bottom_y, 0)
        return float(pixel_distance) / settings.PIXELS_PER_METER

    def get_distance_to_edge(self, bbox: List[int], frame_height: int) -> Optional[float]:
        """Return the current bottom-edge distance in meters."""
        return self._distance_to_bottom_edge_meters(bbox, frame_height)

    def update(self, track_id: int, bbox: List[int], frame_height: int) -> float:
        """Update cumulative time inside the safety limit zone for a tracked person."""
        now = datetime.utcnow()
        distance_meters = self._distance_to_bottom_edge_meters(bbox, frame_height)
        if distance_meters is None:
            self.track_last_update[track_id] = now
            return self.track_in_zone_seconds.get(track_id, 0.0)

        last_update = self.track_last_update.get(track_id)
        self.track_last_update[track_id] = now

        elapsed_seconds = 0.0
        if last_update is not None:
            elapsed_seconds = (now - last_update).total_seconds()

        if distance_meters <= settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS:
            self.track_in_zone_seconds[track_id] += elapsed_seconds
        return self.track_in_zone_seconds[track_id]

    def detect(self, frame, poses):
        """Legacy compatibility method for danger-zone detections."""
        if frame is None or poses is None:
            return []
        frame_h, frame_w = frame.shape[:2]
        alerts = []
        for pose in poses:
            distance = self.get_distance_to_edge(pose.get("bounding_box") or pose.get("bbox"), frame_h)
            if distance is not None and distance <= settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS:
                alerts.append({"pose": pose, "distance_to_edge": distance})
        return alerts
