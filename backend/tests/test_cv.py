"""Computer vision tests"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.cv.tracker import ObjectTracker


def test_detector():
    """Test object detector"""
    tracker = ObjectTracker()
    tracks = tracker.update(
        [
            {"bounding_box": [10, 10, 50, 80], "confidence": 0.95},
            {"bounding_box": [60, 15, 90, 85], "confidence": 0.88},
        ]
    )
    assert isinstance(tracks, dict)
    assert len(tracks) == 2


def test_pose_estimator():
    """Test pose estimator"""
    tracker = ObjectTracker()
    tracks = tracker.update([{"bounding_box": [0, 0, 20, 20]}])
    assert any(track.get("center") for track in tracks.values())
