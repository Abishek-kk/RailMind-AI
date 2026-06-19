"""
DEPRECATED: This module is no longer used.

Architecture:
- Real-time behavioral analysis (video_processor.py) uses 7 BEHAVIORAL features:
  * edge_proximity_seconds, loitering_time, pacing_count, movement_speed,
    direction_changes, following_distance, crowd_interactions
  These are extracted from detector classes (EdgeProximityDetector, LoiteringDetector, etc)
  and fed to the LSTM behavior analyzer.

- Offline training now uses SYNTHETIC data (app/lstm/train.py):
  Generates realistic 7-feature behavioral sequences for 4 classes:
  * Normal, Suicide Risk, Pickpocketing, Security Threat
  Trains one 4-class classifier without needing pose-geometric features.

This file previously extracted geometric pose features (mean/std, distances, angles)
for offline training, but that approach has been replaced by synthetic data generation.
Remove this file.
"""

# This class is deprecated. Use app.lstm.train for synthetic data generation.
# Reference: app/cv/video_processor.py for the current feature extraction pipeline.
