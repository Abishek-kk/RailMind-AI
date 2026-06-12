from typing import Dict, Any

def perception_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Perception Agent
    Ingests raw Computer Vision and LSTM data and structures it into a clear observation.
    """
    raw_data = state.get("raw_data", {})
    
    lstm_scores = raw_data.get("lstm_scores", {})
    lstm_score = raw_data.get("lstm_score")
    if lstm_score is None:
        lstm_score = max(lstm_scores.values()) if lstm_scores else raw_data.get("lstm_anomaly_score", 0.0)
    lstm_anomaly_score = raw_data.get("lstm_anomaly_score", lstm_scores.get("anomaly", 0.0))
    edge_distance = raw_data.get("edge_distance_meters", 5.0)
    duration_seconds = raw_data.get("behavior_duration_seconds", 0)
    edge_proximity_seconds = raw_data.get("edge_proximity_seconds", raw_data.get("edge_time_seconds", 0.0))
    pose_classification = raw_data.get("pose_classification", "normal")
    context_multiplier = raw_data.get("context_multiplier", 1.0)

    structured_observation = {
        "person_id": raw_data.get("person_id", "unknown"),
        "camera_id": raw_data.get("camera_id", "unknown"),
        "platform": raw_data.get("platform", "unknown"),
        "lstm_score": lstm_score,
        "lstm_anomaly_score": lstm_anomaly_score,
        "lstm_scores": lstm_scores,
        "edge_distance": edge_distance,
        "edge_distance_meters": edge_distance,
        "edge_proximity_seconds": edge_proximity_seconds,
        "edge_time_seconds": edge_proximity_seconds,
        "duration_seconds": duration_seconds,
        "behavior_duration_seconds": duration_seconds,
        "pose_classification": pose_classification,
        "following_distance": raw_data.get("following_distance"),
        "speed_mps": raw_data.get("speed_mps", raw_data.get("movement_speed", 0.0)),
        "movement_speed": raw_data.get("movement_speed", raw_data.get("speed_mps", 0.0)),
        "direction_changes": raw_data.get("direction_changes", 0),
        "loitering_duration": raw_data.get("loitering_duration", 0),
        "track_intrusion": raw_data.get("track_intrusion", False),
        "context_multiplier": context_multiplier,
        "bounding_box": raw_data.get("bounding_box", []),
        "metadata": raw_data.get("metadata", {}),
    }

    return {"observation": structured_observation}
