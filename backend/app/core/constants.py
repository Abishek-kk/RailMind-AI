"""Application constants and configuration values"""

# Behavior detection confidence thresholds
CONFIDENCE_THRESHOLD_ALERT = 0.7
CONFIDENCE_THRESHOLD_WARNING = 0.5

# Behavior type identifiers
BEHAVIOR_TYPES = {
    "normal": 0,
    "suicide_risk": 1,
    "pickpocketing": 2,
    "loitering": 3,
    "track_intrusion": 4,
    "suspicious_following": 5
}

# Temporal transformer sequence settings
SEQUENCE_LENGTH = 30
FEATURE_DIMENSION = 17

# Alert severity levels
SEVERITY_LEVELS = {
    "INFO": "info",
    "WARNING": "warning",
    "CRITICAL": "critical"
}
