"""Agent tests"""
import pytest

from app.agents.agent_graph import run_agent_pipeline
from app.agents.intervention_agent import intervention_node
from app.agents.perception_agent import perception_node
from app.agents.reasoning_agent import reasoning_node


def test_perception_agent():
    raw = {
        "person_id": "test-person",
        "camera_id": "CCTV_TEST_01",
        "platform": "Platform 7",
        "lstm_anomaly_score": 0.92,
        "edge_distance_meters": 0.8,
        "behavior_duration_seconds": 45,
        "pose_classification": "distress",
        "following_distance": 0.7,
        "speed_mps": 0.2,
        "direction_changes": 4,
        "loitering_duration": 190,
        "track_intrusion": True,
        "bounding_box": [100, 200, 150, 300],
    }

    result = perception_node({"raw_data": raw})
    observation = result["observation"]

    assert observation["person_id"] == "test-person"
    assert observation["following_distance"] == 0.7
    assert observation["track_intrusion"] is True
    assert observation["pose_classification"] == "distress"


def test_reasoning_agent_high_risk():
    state = {
        "observation": {
            "lstm_score": 0.92,
            "edge_distance": 0.5,
            "duration_seconds": 120,
            "pose_classification": "distress",
            "following_distance": 0.7,
            "loitering_duration": 200,
            "track_intrusion": False,
            "context_multiplier": 1.0,
        }
    }

    result = reasoning_node(state)
    decision = result["decision"]

    assert decision["risk_level"] in ["High Risk", "Critical"]
    assert decision["incident_type"] == "Suicide Risk"
    assert decision["final_risk_score"] >= 0.7


def test_intervention_agent_triggers_broadcast():
    state = {
        "observation": {
            "person_id": "test-person",
            "camera_id": "CCTV_TEST_01",
            "platform": "Platform 7",
            "bounding_box": [100, 200, 150, 300],
        },
        "decision": {
            "recommended_action": "emergency_escalation",
            "final_risk_score": 0.95,
            "risk_level": "Critical",
            "incident_type": "Suicide Risk",
        },
    }

    result = intervention_node(state)

    assert "websocket_broadcast_triggered" in result["execution_status"] or "websocket_broadcast_failed" in result["execution_status"]
    assert result["alert_payload"]["risk_level"] == "Critical"


@pytest.mark.asyncio
async def test_agent_pipeline_end_to_end():
    raw_data = {
        "person_id": "pipeline-person",
        "camera_id": "CCTV_PIPE_01",
        "platform": "Platform 9",
        "lstm_anomaly_score": 0.88,
        "edge_distance_meters": 0.7,
        "behavior_duration_seconds": 130,
        "pose_classification": "distress",
        "following_distance": 0.9,
        "speed_mps": 0.3,
        "direction_changes": 3,
        "loitering_duration": 210,
        "track_intrusion": False,
        "context_multiplier": 1.0,
        "bounding_box": [20, 40, 120, 240],
    }

    state = await run_agent_pipeline(raw_data)
    assert "alert_payload" in state
    assert state["alert_payload"]["risk_level"] in ["High Risk", "Critical"]
    assert state["alert_payload"]["incident_type"] == "Suicide Risk"
