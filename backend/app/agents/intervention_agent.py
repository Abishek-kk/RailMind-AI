from typing import Dict, Any
from datetime import datetime


def intervention_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3: Intervention Agent
    Triggers appropriate responses based on the reasoning decision.
    """
    obs = state.get("observation", {})
    decision = state.get("decision", {})
    
    action = decision.get("recommended_action")
    
    alert_payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "person_id": obs.get("person_id"),
        "camera_id": obs.get("camera_id"),
        "platform": obs.get("platform"),
        "incident_type": decision.get("incident_type"),
        "risk_score": decision.get("final_risk_score"),
        "risk_level": decision.get("risk_level"),
        "bounding_box": obs.get("bounding_box"),
        "metadata": obs.get("metadata", {}),
    }
    
    execution_status = []

    if action in ["alert_staff", "urgent_alert", "emergency_escalation"]:
        # Indicate a websocket broadcast is required for the frontend and persistence flow.
        execution_status.append("websocket_broadcast_required")
        execution_status.append("email_alert_required")

    if action == "emergency_escalation":
        execution_status.append("sms_escalation_required")

    if action in ["passive_monitor", "log_only"]:
        execution_status.append("logged_to_database")
        
    return {
        "alert_payload": alert_payload,
        "execution_status": execution_status
    }
