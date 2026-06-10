"""
Computer Vision Processing Package

Combines frame ingestion, pose skeleton extraction, and temporal behavior analysis.

Components:
- PoseEstimator: YOLOv8-pose model for person detection and keypoint extraction
- BehaviorAnalyzer: LSTM-based temporal behavior analysis
- VideoProcessor: Main processing pipeline for camera feed streams
"""

from .pose_estimator import PoseEstimator
from .lstm_behavior import BehaviorAnalyzer
from .video_processor import VideoProcessor

__all__ = [
    "PoseEstimator",
    "BehaviorAnalyzer",
    "VideoProcessor",
]