"""
DEPRECATED: This module is no longer used.

Architecture:
- Real-time behavioral analysis (video_processor.py) uses 7 BEHAVIORAL features:
  * edge_proximity_seconds, loitering_time, pacing_count, movement_speed,
    direction_changes, following_distance, crowd_interactions
  These are extracted from detector classes (EdgeProximityDetector, LoiteringDetector, etc)
  and fed to the transformer behavior analyzer.

- Offline training now uses SYNTHETIC data (app.transformer.train.py):
  Generates realistic 7-feature behavioral sequences for 4 classes:
  * Normal, Suicide Risk, Pickpocketing, Security Threat
  Trains one 4-class classifier without needing pose-geometric features.

This file previously extracted geometric pose features (mean/std, distances, angles)
for offline training, but that approach has been replaced by synthetic data generation.
Remove this file.
"""

# This class is deprecated. Use app.transformer.train for synthetic data generation.
# Reference: app/cv/video_processor.py for the current feature extraction pipeline.

from typing import List

def extract_pose_features(yolo_keypoints: List[List[float]]) -> List[float]:
  """
  Converts 17 coordinate keypoints [x, y, confidence] into a normalized flat 34-feature list.
  Normalizes coordinates relative to the person's bounding container for scale invariance.
  """
  if not yolo_keypoints or len(yolo_keypoints) < 17:
    return [0.0] * 34
        
  x_coords = [kp[0] for kp in yolo_keypoints if len(kp) > 0 and kp[0] > 0]
  y_coords = [kp[1] for kp in yolo_keypoints if len(kp) > 1 and kp[1] > 0]
    
  # Handle edge case where skeleton acquisition is completely dropped
  if not x_coords or not y_coords:
    return [0.0] * 34
        
  # Isolate bounding extremes
  min_x, max_x = min(x_coords), max(x_coords)
  min_y, max_y = min(y_coords), max(y_coords)
    
  box_width = (max_x - min_x) if (max_x - min_x) > 0 else 1.0
  box_height = (max_y - min_y) if (max_y - min_y) > 0 else 1.0
    
  flat_features = []
  for kp in yolo_keypoints:
    # Enforce bounding-box local min-max coordinate calculation scaling
    norm_x = (kp[0] - min_x) / box_width
    norm_y = (kp[1] - min_y) / box_height
    flat_features.extend([norm_x, norm_y])
        
  return flat_features
