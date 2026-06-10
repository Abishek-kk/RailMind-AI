"""
Behavioral Feature Detectors for Real-Time Platform Safety Monitoring.

These detectors extract behavioral features from pose tracking data:
- EdgeProximityDetector: Distance and time near platform edges
- LoiteringDetector: Prolonged stationary behavior
- PacingDetector: Repetitive movement patterns
- FollowingDetector: Inter-person distance and crowd interactions
- MovementAnalyzer: Speed and direction change analysis

Features are aggregated into a 7-element behavioral vector consumed by the LSTM.
For training data generation, use app.lstm.train for synthetic behavioral sequences.
"""

from .edge_proximity import EdgeProximityDetector
from .following_detector import FollowingDetector
from .loitering_detector import LoiteringDetector
from .movement_analyzer import MovementAnalyzer
from .pacing_detector import PacingDetector

__all__ = [
    "EdgeProximityDetector",
    "FollowingDetector",
    "LoiteringDetector",
    "MovementAnalyzer",
    "PacingDetector",
]
