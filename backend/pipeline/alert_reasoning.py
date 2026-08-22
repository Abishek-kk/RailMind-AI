"""Generate auditable explanations for alerts from observed pipeline signals."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Mapping


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _explain_alert_rule_based(alert: Mapping[str, Any]) -> dict[str, Any]:
    """Explain an alert using only the behavior signals recorded by the pipeline."""
    activity = str(alert.get("activity", ""))
    evidence: list[dict[str, Any]] = []

    frames_in_track_zone = int(_number(alert.get("frames_in_track_zone")))
    if alert.get("currently_in_track_zone"):
        evidence.append({
            "signal": "currently_in_track_zone",
            "value": True,
            "meaning": "The person's detected feet are currently inside the calibrated track or danger zone.",
        })
    elif alert.get("ever_entered_track_zone"):
        evidence.append({
            "signal": "ever_entered_track_zone",
            "value": True,
            "meaning": "The person's detected feet entered the calibrated track or danger zone during tracking.",
        })

    if frames_in_track_zone:
        evidence.append({
            "signal": "frames_in_track_zone",
            "value": frames_in_track_zone,
            "meaning": "The track-zone signal was observed across multiple video frames.",
        })

    duration = _number(alert.get("duration_tracked_s"))
    if duration > 0:
        evidence.append({
            "signal": "duration_tracked_s",
            "value": round(duration, 1),
            "meaning": "The person was tracked for this many seconds in the analyzed footage.",
        })

    if alert.get("loitering_detected"):
        evidence.append({
            "signal": "loitering_detected",
            "value": True,
            "meaning": "The person remained within the platform zone beyond the configured dwell threshold with limited movement.",
        })

    reversals = int(_number(alert.get("direction_reversals")))
    if reversals:
        evidence.append({
            "signal": "direction_reversals",
            "value": reversals,
            "meaning": "The movement path changed direction abruptly this many times.",
        })

    if not evidence:
        evidence.append({
            "signal": "activity",
            "value": activity or "unknown",
            "meaning": "The pipeline marked this track as anomalous, but no supporting telemetry was stored.",
        })

    if activity in {"IN_DANGER_ZONE", "PREVIOUSLY_IN_DANGER_ZONE"}:
        summary = "Alert raised because the tracked person's feet entered the calibrated danger zone."
    elif activity == "LOITERING_ON_PLATFORM":
        summary = "Alert raised because the tracked person remained in the platform zone with limited movement beyond the dwell threshold."
    elif activity == "ERRATIC_MOVEMENT":
        summary = "Alert raised because the tracked person's movement included repeated abrupt direction reversals."
    else:
        summary = "Alert raised from an anomalous behavior signal recorded by the video pipeline."

    return {
        "mode": "rule_based",
        "summary": summary,
        "evidence": evidence,
        "limitations": "This explanation describes observed position and movement signals; it does not determine intent or identity.",
    }


def _valid_gemini_result(result: Any) -> bool:
    return (
        isinstance(result, dict)
        and isinstance(result.get("summary"), str)
        and bool(result["summary"].strip())
        and isinstance(result.get("evidence"), list)
        and all(
            isinstance(item, dict)
            and isinstance(item.get("signal"), str)
            and isinstance(item.get("meaning"), str)
            for item in result["evidence"]
        )
        and isinstance(result.get("limitations"), str)
        and bool(result["limitations"].strip())
    )


@lru_cache(maxsize=256)
def _gemini_reasoning(alert_json: str, model_name: str, api_key: str) -> dict[str, Any] | None:
    """Generate one cached Gemini explanation, returning None on any integration failure."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=(
                "Explain this video safety alert using only the supplied observed telemetry. "
                "Do not infer intent, identity, emotions, or facts that are not present. "
                "Return JSON with exactly these fields: summary (string), evidence (array "
                "of objects with signal, value, and meaning), and limitations (string).\n\n"
                f"Alert telemetry:\n{alert_json}"
            ),
            config={"response_mime_type": "application/json"},
        )
        result = json.loads(response.text or "")
        if not _valid_gemini_result(result):
            return None
        result["mode"] = "llm"
        return result
    except Exception:
        return None


def explain_alert(alert: Mapping[str, Any], use_llm: bool = True) -> dict[str, Any]:
    """Use Gemini when requested and configured, with a deterministic fallback."""
    fallback = _explain_alert_rule_based(alert)
    if not use_llm:
        return fallback
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback

    model_name = os.getenv("GEMINI_REASONING_MODEL", "gemini-2.5-flash").strip()
    alert_json = json.dumps(dict(alert), sort_keys=True, default=str)
    result = _gemini_reasoning(alert_json, model_name, api_key)
    return result if result is not None else fallback