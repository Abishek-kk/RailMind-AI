"""Agent tests"""
import sys
import types

import pytest

import app.agents.agent_graph as agent_graph
import app.agents.reasoning_agent as reasoning_agent
from app.agents.agent_graph import run_agent_pipeline
from app.agents.intervention_agent import intervention_node
from app.agents.perception_agent import perception_node
from app.agents.reasoning_agent import reasoning_node
from app.core.config import settings


def test_perception_agent():
    raw = {
        "person_id": "test-person",
        "camera_id": "CCTV_TEST_01",
        "platform": "Platform 7",
        "transformer_anomaly_score": 0.92,
        "transformer_scores": {"suicide": 0.84, "pickpocket": 0.12, "anomaly": 0.31},
        "edge_distance_meters": 0.8,
        "edge_proximity_seconds": 12.5,
        "behavior_duration_seconds": 45,
        "pose_classification": "distress",
        "following_distance": 0.7,
        "movement_speed": 0.2,
        "direction_changes": 4,
        "loitering_duration": 190,
        "track_intrusion": True,
        "bounding_box": [100, 200, 150, 300],
    }

    result = perception_node({"raw_data": raw})
    observation = result["observation"]

    assert observation["person_id"] == "test-person"
    assert observation["transformer_score"] == 0.84
    assert observation["transformer_anomaly_score"] == 0.92
    assert observation["transformer_scores"] == {"suicide": 0.84, "pickpocket": 0.12, "anomaly": 0.31}
    assert observation["edge_proximity_seconds"] == 12.5
    assert observation["edge_time_seconds"] == 12.5
    assert observation["following_distance"] == 0.7
    assert observation["movement_speed"] == 0.2
    assert observation["loitering_duration"] == 190
    assert observation["track_intrusion"] is True
    assert observation["pose_classification"] == "distress"


def test_reasoning_agent_high_risk():
    state = {
        "observation": {
            "transformer_score": 0.92,
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


def test_reasoning_agent_uses_dominant_transformer_score_before_anomaly_score():
    state = {
        "observation": {
            "transformer_score": 0.9,
            "transformer_anomaly_score": 0.1,
            "edge_distance": 3.0,
            "duration_seconds": 0,
            "pose_classification": "normal",
            "following_distance": None,
            "loitering_duration": 0,
            "context_multiplier": 1.0,
        }
    }

    result = reasoning_node(state)

    assert result["decision"]["final_risk_score"] == 36


def test_openai_reasoning_uses_current_responses_client(monkeypatch):
    calls = {}

    class DummyResponses:
        def create(self, **kwargs):
            calls.update(kwargs)
            return types.SimpleNamespace(
                output_text='{"reasoning_summary":"ok","risk_adjustment":5,"recommended_action_override":"dispatch_staff"}'
            )

    class DummyOpenAI:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.responses = DummyResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_REASONING_MODEL", "gpt-test-model")

    result = reasoning_agent._get_llm_reasoning({"pose_classification": "normal"}, 40, "monitor")

    assert result["risk_adjustment"] == 5
    assert calls["api_key"] == "openai-test-key"
    assert calls["model"] == "gpt-test-model"
    assert isinstance(calls["input"], list)
    assert calls["input"][0]["role"] == "system"


def test_anthropic_reasoning_uses_current_messages_client(monkeypatch):
    calls = {}

    class DummyMessages:
        def create(self, **kwargs):
            calls.update(kwargs)
            return types.SimpleNamespace(
                content=[
                    types.SimpleNamespace(
                        text='{"reasoning_summary":"ok","risk_adjustment":-3,"recommended_action_override":null}'
                    )
                ]
            )

    class DummyAnthropic:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.messages = DummyMessages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=DummyAnthropic))
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setattr(settings, "ANTHROPIC_REASONING_MODEL", "claude-test-model")

    result = reasoning_agent._get_llm_reasoning({"pose_classification": "normal"}, 40, "monitor")

    assert result["risk_adjustment"] == -3
    assert calls["api_key"] == "anthropic-test-key"
    assert calls["model"] == "claude-test-model"
    assert calls["messages"][0]["role"] == "user"
    assert "system" in calls


def test_llm_reasoning_failure_falls_back_to_rule_based(monkeypatch):
    class ExplodingResponses:
        def create(self, **kwargs):
            raise RuntimeError("network unavailable")

    class DummyOpenAI:
        def __init__(self, api_key):
            self.responses = ExplodingResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")

    state = {
        "observation": {
            "transformer_score": 0.9,
            "edge_distance": 3.0,
            "duration_seconds": 0,
            "pose_classification": "normal",
            "following_distance": None,
            "loitering_duration": 0,
            "context_multiplier": 1.0,
        }
    }

    result = reasoning_node(state)

    assert result["decision"]["final_risk_score"] == 36
    assert result["decision"]["reasoning_summary"] is None
    assert result["decision"]["reasoning_mode"] == "rule_based"


def test_reasoning_node_marks_rule_based_when_no_api_keys():
    original_openai = settings.OPENAI_API_KEY
    original_anthropic = settings.ANTHROPIC_API_KEY
    try:
        settings.OPENAI_API_KEY = ""
        settings.ANTHROPIC_API_KEY = ""

        state = {
            "observation": {
                "transformer_score": 0.5,
                "edge_distance": 2.0,
                "duration_seconds": 30,
                "pose_classification": "normal",
                "following_distance": None,
                "loitering_duration": 0,
                "context_multiplier": 1.0,
            }
        }

        result = reasoning_node(state)
        assert result["decision"]["reasoning_mode"] == "rule_based"
    finally:
        settings.OPENAI_API_KEY = original_openai
        settings.ANTHROPIC_API_KEY = original_anthropic


def test_reasoning_node_marks_llm_when_api_key_configured(monkeypatch):
    class DummyResponses:
        def create(self, **kwargs):
            return types.SimpleNamespace(
                output_text='{"reasoning_summary":"test summary","risk_adjustment":0,"recommended_action_override":null}'
            )

    class DummyOpenAI:
        def __init__(self, api_key):
            self.responses = DummyResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")

    state = {
        "observation": {
            "transformer_score": 0.5,
            "edge_distance": 2.0,
            "duration_seconds": 30,
            "pose_classification": "normal",
            "following_distance": None,
            "loitering_duration": 0,
            "context_multiplier": 1.0,
        }
    }

    result = reasoning_node(state)
    assert result["decision"]["reasoning_mode"] == "llm"
    assert result["decision"]["reasoning_summary"] == "test summary"


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

    assert "websocket_broadcast_required" in result["execution_status"] or "websocket_broadcast_failed" in result["execution_status"]
    assert result["alert_payload"]["risk_level"] == "Critical"


def test_intervention_agent_alerts_staff_for_low_risk_action():
    state = {
        "observation": {
            "person_id": "test-person",
            "camera_id": "CCTV_TEST_01",
            "platform": "Platform 7",
        },
        "decision": {
            "recommended_action": "alert_staff",
            "final_risk_score": 50,
            "risk_level": "Low Risk",
            "incident_type": "Loitering",
        },
    }

    result = intervention_node(state)

    assert "websocket_broadcast_required" in result["execution_status"]
    assert "email_alert_required" in result["execution_status"]


@pytest.mark.asyncio
async def test_agent_pipeline_end_to_end():
    raw_data = {
        "person_id": "pipeline-person",
        "camera_id": "CCTV_PIPE_01",
        "platform": "Platform 9",
        "transformer_anomaly_score": 0.88,
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
    assert state["alert_payload"]["risk_level"] in ["Medium Risk", "High Risk", "Critical"]
    assert state["alert_payload"]["incident_type"] == "Suicide Risk"


@pytest.mark.asyncio
async def test_agent_pipeline_builds_graph_per_invocation(monkeypatch):
    # With the pipeline compiled once at module import, run_agent_pipeline
    # should NOT rebuild the graph on every invocation. To assert this,
    # clear the compiled singleton and monkeypatch `build_agent_graph` to
    # count how many times it is invoked. The lazy compile fallback should
    # call the builder only once and reuse the compiled pipeline thereafter.
    build_count = 0

    class DummyPipeline:
        def invoke(self, state):
            return {"state": state, "execution_status": ["ok"]}

    def build_dummy_graph():
        nonlocal build_count
        build_count += 1
        return DummyPipeline()

    # Ensure we start with no compiled pipeline so the lazy compile path runs
    monkeypatch.setattr(agent_graph, "_COMPILED_AGENT_PIPELINE", None)
    monkeypatch.setattr(agent_graph, "build_agent_graph", build_dummy_graph)

    await agent_graph.run_agent_pipeline({"person_id": "one"})
    await agent_graph.run_agent_pipeline({"person_id": "two"})

    # Should have built exactly once and reused thereafter
    assert build_count == 1
