import json
import logging
from typing import Dict, Any

from app.core.config import settings
from app.services.risk_scoring import RiskScorer

logger = logging.getLogger("railmind")


def reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Reasoning Agent
    Delegates risk scoring to the central RiskScorer service and optionally applies LLM-based reasoning.
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

    llm_response = _get_llm_reasoning(obs, final_risk_score, action)
    if llm_response:
        adjustment = llm_response.get("risk_adjustment", 0)
        if not isinstance(adjustment, int):
            try:
                adjustment = int(adjustment)
            except (TypeError, ValueError):
                adjustment = 0

        adjustment = max(-10, min(10, adjustment))
        final_risk_score = max(0, min(100, final_risk_score + adjustment))
        risk_level, action = scorer.classify(final_risk_score)
        recommended_action = llm_response.get("recommended_action_override") or action
        reasoning_summary = llm_response.get("reasoning_summary")
    else:
        recommended_action = action
        reasoning_summary = None

    decision = {
        "final_risk_score": final_risk_score,
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "incident_type": determine_incident_type(obs, pose),
        "reasoning_summary": reasoning_summary,
    }

    return {"decision": decision}


def _get_llm_reasoning(observation: Dict[str, Any], score: float, action: str) -> Dict[str, Any]:
    openai_api_key = settings.OPENAI_API_KEY.strip()
    anthropic_api_key = settings.ANTHROPIC_API_KEY.strip()
    if not openai_api_key and not anthropic_api_key:
        return {}

    prompt = _build_llm_prompt(observation, score, action)

    if openai_api_key:
        response_text = _call_openai_reasoning(prompt, openai_api_key)
    else:
        response_text = _call_anthropic_reasoning(prompt, anthropic_api_key)

    if not response_text:
        return {}

    return _parse_llm_json(response_text)


def _call_openai_reasoning(prompt: str, api_key: str) -> str:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=settings.OPENAI_REASONING_MODEL,
            input=[
                {
                    "role": "system",
                    "content": "You are a security reasoning assistant that returns valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_output_tokens=512,
        )
        return getattr(response, "output_text", "") or ""
    except Exception as exc:
        logger.warning("OpenAI reasoning failed, falling back to rule-based behavior: %s", exc)
        return ""


def _call_anthropic_reasoning(prompt: str, api_key: str) -> str:
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=settings.ANTHROPIC_REASONING_MODEL,
            max_tokens=512,
            temperature=0.0,
            system="You are a security reasoning assistant that returns valid JSON only.",
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_anthropic_text(response)
    except Exception as exc:
        logger.warning("Anthropic reasoning failed, falling back to rule-based behavior: %s", exc)
        return ""


def _extract_anthropic_text(response: Any) -> str:
    chunks = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def _build_llm_prompt(observation: Dict[str, Any], score: float, action: str) -> str:
    return (
        "Given the following observation and the current rule-based risk score, "
        "provide a concise JSON response with fields: reasoning_summary (string), "
        "risk_adjustment (integer between -10 and +10), and recommended_action_override "
        "(string or null). Do not include any additional text outside the JSON object.\n\n"
        f"Observation: {json.dumps(observation, default=str)}\n"
        f"Rule-based risk score: {score}\n"
        f"Rule-based recommended action: {action}\n"
        "Respond with valid JSON only."
    )


def _parse_llm_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    trimmed = text.strip()
    if not trimmed:
        return {}

    try:
        return json.loads(trimmed)
    except json.JSONDecodeError:
        start = trimmed.find("{")
        end = trimmed.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(trimmed[start:end + 1])
            except json.JSONDecodeError:
                pass
    logger.warning("Failed to parse LLM reasoning JSON from response: %s", trimmed)
    return {}


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
