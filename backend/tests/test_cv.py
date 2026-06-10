"""Computer vision tests"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.cv import PoseEstimator, VideoProcessor


def test_pose_estimator_import():
    """Test that PoseEstimator is available"""
    assert PoseEstimator is not None


def test_video_processor_import():
    """Test that VideoProcessor is available"""
    assert VideoProcessor is not None
