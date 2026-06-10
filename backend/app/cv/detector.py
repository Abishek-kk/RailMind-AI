"""
DEPRECATED: This module is no longer used.

PersonDetector was replaced by PoseEstimator which combines:
- Person detection (YOLOv8)
- Pose keypoint extraction (YOLOv8-pose)

In a single efficient forward pass. Using PoseEstimator directly from video_processor.py
eliminates the need for a separate detection step.

This file is kept for reference only. All imports have been removed from cv/__init__.py.
Consider removing this file.
"""