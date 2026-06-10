"""Validation utilities for input validation"""

def validate_frame(frame):
    """Validate video frame format"""
    if frame is None or not isinstance(frame, dict):
        raise ValueError("Frame must be a dict containing width and height")
    if "width" not in frame or "height" not in frame:
        raise ValueError("Frame dictionary must include width and height")
    return True

def validate_pose(pose):
    """Validate pose keypoints"""
    if pose is None:
        raise ValueError("Pose must be provided")
    if not isinstance(pose, (list, tuple)):
        raise ValueError("Pose must be a list or tuple of keypoints")
    if len(pose) == 0:
        raise ValueError("Pose must include at least one keypoint")
    return True

def validate_alert_data(alert_data):
    """Validate alert data structure"""
    if not isinstance(alert_data, dict):
        raise ValueError("Alert data must be a dictionary")
    required_fields = ["person_id", "camera_id", "platform", "incident_type", "risk_score", "risk_level"]
    missing = [field for field in required_fields if field not in alert_data]
    if missing:
        raise ValueError(f"Missing required alert fields: {missing}")
    validate_confidence_score(alert_data.get("risk_score"))
    return True

def validate_confidence_score(score):
    """Validate confidence score is between 0-1"""
    if score is None:
        raise ValueError("Score cannot be None")
    try:
        value = float(score)
    except (TypeError, ValueError):
        raise ValueError("Score must be a number between 0 and 1")
    if not 0.0 <= value <= 1.0:
        raise ValueError("Score must be between 0 and 1")
    return True
