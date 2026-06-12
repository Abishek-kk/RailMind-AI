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
    api_key = settings.OPENAI_API_KEY.strip() or settings.ANTHROPIC_API_KEY.strip()
    if not api_key:
        return {}

    prompt = _build_llm_prompt(observation, score, action)
    response_text = ""

    if settings.OPENAI_API_KEY.strip():
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a security reasoning assistant that returns valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            response_text = completion.choices[0].message.content
        except Exception as exc:
            logger.warning("OpenAI reasoning failed, falling back to rule-based behavior: %s", exc)
            return {}
    elif settings.ANTHROPIC_API_KEY.strip():
        try:
            import anthropic
            client = anthropic.Client(settings.ANTHROPIC_API_KEY)
            response = client.complete(
                prompt=anthropic.HUMAN_PROMPT + prompt + anthropic.AI_PROMPT,
                model="claude-3.5-mini",
                max_tokens_to_sample=512,
                temperature=0.0,
            )
            response_text = response.completion
        except Exception as exc:
            logger.warning("Anthropic reasoning failed, falling back to rule-based behavior: %s", exc)
            return {}

    return _parse_llm_json(response_text)


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
