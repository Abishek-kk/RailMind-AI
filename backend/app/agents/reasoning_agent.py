from typing import Dict, Any
from app.core.config import settings
from app.services.risk_scoring import RiskScorer

def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Reasoning Agent
    Delegates risk scoring to the central RiskScorer service.
    """
    obs = state.get("observation", {})
    scorer = RiskScorer()

    score_input = {
        "lstm_score": obs.get("lstm_score", obs.get("lstm_anomaly_score", 0.0)),
        "edge_distance": obs.get("edge_distance", obs.get("edge_distance_meters", settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS * 2)),
        "duration_seconds": obs.get("behavior_duration_seconds", obs.get("duration_seconds", 0)),
        "loitering_duration": obs.get("loitering_duration", 0),
        "following_distance": obs.get("following_distance"),
        "pose_classification": obs.get("pose_classification", "normal"),
        "context_multiplier": obs.get("context_multiplier", 1.0),
        "track_intrusion": obs.get("track_intrusion", False),
    }

    final_risk_score = scorer.calculate(score_input)
    risk_level, action = scorer.classify(final_risk_score)
    pose = score_input["pose_classification"]

    decision = {
        "final_risk_score": final_risk_score,
        "risk_level": risk_level,
        "recommended_action": action,
        "incident_type": determine_incident_type(obs, pose)
    }

    return {"decision": decision}


def determine_incident_type(obs: dict, pose: str) -> str:
    """Helper function to classify the specific incident type."""
    if obs.get("track_intrusion"):
        return "Track Intrusion"
    edge_distance = obs.get("edge_distance", obs.get("edge_distance_meters", 5.0))
    if pose == "distress" and edge_distance < settings.PLATFORM_EDGE_SAFETY_LIMIT_METERS:
        return "Suicide Risk"
    if obs.get("following_distance") is not None and obs["following_distance"] < settings.BEHAVIOR_FOLLOWING_DISTANCE_METERS:
        return "Pickpocketing"
    if obs.get("loitering_duration", obs.get("behavior_duration_seconds", 0)) >= 180:
        return "Loitering"
    if pose in ["suspicious", "following"]:
        return "Suspicious Following"
    return "Normal Activity"
