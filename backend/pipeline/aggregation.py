"""
aggregation.py

Turns raw stored pipeline results (results_store.py) into the shapes
the dashboard endpoints need. This is where "activity" labels from
pipeline.py get turned into incident/alert records.

IMPORTANT -- what these labels actually mean:
    IN_DANGER_ZONE / PREVIOUSLY_IN_DANGER_ZONE
        A person's feet were geometrically inside the calibrated
        track/danger zone polygon. This is a literal position fact,
        not an inferred intent. Labeled here as "Track Zone Intrusion".
    LOITERING_ON_PLATFORM
        Stationary/pacing in the platform zone beyond the configured
        dwell threshold. Labeled "Loitering / Trespass".
    ERRATIC_MOVEMENT
        3+ sudden direction reversals. Labeled "General Anomalies".
    NORMAL
        No thresholds tripped -- excluded from incidents entirely.

There is no "Suicide Risk Detection" or "Pickpocketing Actions"
classifier anywhere in this pipeline -- it only measures zone position
and movement patterns. If your frontend wants those specific category
names, that's a labeling/business decision to make deliberately, not
something to paper over here silently. Whoever reviews these
incidents should know a "Track Zone Intrusion" entry means exactly
that: someone's feet were detected in the track zone, for whatever
reason.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from . import alert_status_store as status_store
from .alert_reasoning import explain_alert
from . import results_store as store

ACTIVITY_TO_INCIDENT_TYPE = {
    "NORMAL": "Normal Activity",
    "IN_DANGER_ZONE": "Track Zone Intrusion",
    "PREVIOUSLY_IN_DANGER_ZONE": "Track Zone Intrusion",
    "LOITERING_ON_PLATFORM": "Loitering / Trespass",
    "ERRATIC_MOVEMENT": "General Anomalies",
}

RISK_LEVEL_BY_ACTIVITY = {
    "NORMAL": "Low",
    "IN_DANGER_ZONE": "High",
    "PREVIOUSLY_IN_DANGER_ZONE": "Medium",
    "LOITERING_ON_PLATFORM": "Medium",
    "ERRATIC_MOVEMENT": "Low",
}

# Map risk levels to numeric scores (0-100 scale) for frontend display
RISK_LEVEL_TO_SCORE = {
    "High": 85,
    "Medium": 55,
    "Low": 25,
}

HANDLING_LEVEL_BY_ACTIVITY = {
    "NORMAL": "normal",
    "PREVIOUSLY_IN_DANGER_ZONE": "medium",
    "LOITERING_ON_PLATFORM": "medium",
    "ERRATIC_MOVEMENT": "medium",
    "IN_DANGER_ZONE": "high",
}


def _first_annotated_frame_url(data_dir: str, feed_id: str) -> str | None:
    for entry in store.load_all(data_dir):
        if entry.get("feed_id") != feed_id:
            continue

        annotated_path = str(entry.get("annotated_video_path", "")).replace("\\", "/")
        if not annotated_path:
            return None

        base_dir = os.path.join(data_dir, os.path.dirname(annotated_path))
        annotated_dir = os.path.join(base_dir, "annotated")

        candidates = []
        for search_dir in [annotated_dir, base_dir]:
            if not os.path.isdir(search_dir):
                continue
            for name in sorted(os.listdir(search_dir)):
                lower_name = name.lower()
                if lower_name.endswith(".jpg") or lower_name.endswith(".jpeg") or lower_name.endswith(".png"):
                    candidates.append(os.path.join(search_dir, name))

        if not candidates:
            return None

        rel_path = os.path.relpath(candidates[0], data_dir).replace(os.sep, "/")
        return f"/processed/{rel_path}"

    return None


def _iter_incidents(data_dir: str):
    """
    Yields one dict per tracked person. Normal activity remains visible
    as the lowest handling level, while higher-risk activity is promoted.
    Each dict merges the track summary with
    its video/feed context.
    """
    for entry in store.load_all(data_dir):
        for track_id, summary in entry["tracks"].items():
            activity = summary.get("activity", "NORMAL")
            if activity not in ACTIVITY_TO_INCIDENT_TYPE:
                continue
            yield {
                "video_id": entry["video_id"],
                "feed_id": entry["feed_id"],
                "camera_id": entry["camera_id"],
                "processed_at": entry["processed_at"],
                "track_id": track_id,
                "incident_type": ACTIVITY_TO_INCIDENT_TYPE[activity],
                "risk_level": RISK_LEVEL_BY_ACTIVITY.get(activity, "Low"),
                "handling_level": HANDLING_LEVEL_BY_ACTIVITY.get(activity, "normal"),
                "activity": activity,
                **summary,
            }


def dashboard_stats(data_dir: str) -> dict[str, Any]:
    incidents = list(_iter_incidents(data_dir))
    by_type = Counter(i["incident_type"] for i in incidents)
    return {
        "total_incidents": len(incidents),
        "active_alerts": sum(1 for i in incidents if i["risk_level"] == "High"),
        "track_zone_intrusions": by_type.get("Track Zone Intrusion", 0),
        "loitering_trespass": by_type.get("Loitering / Trespass", 0),
        "general_anomalies": by_type.get("General Anomalies", 0),
        "system_status": "Operational",
    }


def incidents_by_cctv(data_dir: str) -> list[dict[str, Any]]:
    counts = Counter(i["camera_id"] for i in _iter_incidents(data_dir))
    return [{"camera_id": cam, "incidents": count} for cam, count in sorted(counts.items())]


def trend(data_dir: str, days: int = 7) -> list[dict[str, Any]]:
    """
    Groups incidents by the date portion of processed_at.
    Returns one row per UTC calendar day in the requested window ending today.
    """
    by_date: dict[str, Counter] = {}
    for i in _iter_incidents(data_dir):
        date_str = i["processed_at"][:10]
        by_date.setdefault(date_str, Counter())[i["incident_type"]] += 1

    rows = []
    today = datetime.now(timezone.utc).date()
    for offset in range(max(days, 0) - 1, -1, -1):
        date_str = (today - timedelta(days=offset)).isoformat()
        counter = by_date.get(date_str, Counter())
        rows.append({
            "date": date_str,
            "Track Zone Intrusion": counter.get("Track Zone Intrusion", 0),
            "Loitering / Trespass": counter.get("Loitering / Trespass", 0),
            "General Anomalies": counter.get("General Anomalies", 0),
        })
    return rows


def risk_distribution(data_dir: str) -> list[dict[str, Any]]:
    counts = Counter(i["incident_type"] for i in _iter_incidents(data_dir))
    return [{"name": name, "value": count} for name, count in counts.items()]


def peak_hours(data_dir: str) -> list[dict[str, Any]]:
    """Groups incidents by the hour portion of processed_at (video processing time,
    not necessarily the time the incident occurred in the footage)."""
    counts: Counter = Counter()
    for i in _iter_incidents(data_dir):
        # processed_at is iso8601, e.g. 2026-08-04T14:20:00+00:00
        hour = i["processed_at"][11:13] + ":00"
        counts[hour] += 1
    return [{"hour": h, "incidents": c} for h, c in sorted(counts.items())]


def cctv_summary(data_dir: str) -> list[dict[str, Any]]:
    entries = store.load_all(data_dir)
    summaries = []
    for entry in entries:
        cam_incidents = [i for i in _iter_incidents(data_dir) if i["camera_id"] == entry["camera_id"]]
        high = [i for i in cam_incidents if i["risk_level"] == "High"]
        summaries.append({
            "camera_id": entry["camera_id"],
            "feed_id": entry["feed_id"],
            "total_incidents": len(cam_incidents),
            "active_alerts": len(high),
            "current_risk_level": "High" if high else ("Medium" if cam_incidents else "Low"),
            "last_incident": max((i["processed_at"] for i in cam_incidents), default=None),
        })
    return summaries


def incidents_list(data_dir: str) -> list[dict[str, Any]]:
    result = []
    for i in _iter_incidents(data_dir):
        risk_score = RISK_LEVEL_TO_SCORE.get(i["risk_level"], 25)
        result.append({
            "id": f"{i['feed_id']}-{i['track_id']}",
            "camera_id": i["camera_id"],
            "incident_type": i["incident_type"],
            "risk_level": i["risk_level"],
            "risk_score": risk_score,
            "status": "active",
            "timestamp": i["processed_at"],
            "track_id": i["track_id"],
            "duration_tracked_s": i.get("duration_tracked_s"),
        })
    return result


def alerts_list(data_dir: str) -> list[dict[str, Any]]:
    """All tracked activities surfaced with an actionable handling level."""
    result = []
    for i in _iter_incidents(data_dir):
        alert_id = f"{i['feed_id']}-{i['track_id']}"
        risk_score = RISK_LEVEL_TO_SCORE.get(i["risk_level"], 25)

        result_entry = store.get_by_feed_id(data_dir, i["feed_id"])
        annotated_path = str(result_entry.get("annotated_video_path", "")).replace("\\", "/") if result_entry else ""
        image_url = _first_annotated_frame_url(data_dir, i["feed_id"])

        # Consult alert_status_store for persisted status/operator
        status_record = status_store.get_status(data_dir, alert_id)
        status = status_record["status"] if status_record else "active"
        operator_assigned = status_record["operator_assigned"] if status_record else None
        handling_level = status_record.get("handling_level", i["handling_level"]) if status_record else i["handling_level"]

        result.append({
            "id": alert_id,
            "person_id": f"P-{i['track_id']}",
            "camera_id": i["camera_id"],
            "incident_type": i["incident_type"],
            "risk_level": i["risk_level"],
            "risk_score": risk_score,
            "status": status,
            "timestamp": i["processed_at"],
            "operator_assigned": operator_assigned,
            "handling_level": handling_level,
            "escalation_reason": status_record.get("escalation_reason") if status_record else None,
            "escalated_at": status_record.get("escalated_at") if status_record else None,
            "confirmed_by": status_record.get("confirmed_by") if status_record else None,
            "confirmation_reason": status_record.get("confirmation_reason") if status_record else None,
            "activity": i.get("activity"),
            "frames_in_track_zone": i.get("frames_in_track_zone", 0),
            "currently_in_track_zone": i.get("currently_in_track_zone", False),
            "ever_entered_track_zone": i.get("ever_entered_track_zone", False),
            "loitering_detected": i.get("loitering_detected", False),
            "direction_reversals": i.get("direction_reversals", 0),
            "duration_tracked_s": i.get("duration_tracked_s"),
            "video_snippet_url": f"/processed/{annotated_path}" if annotated_path else None,
            "image_url": image_url,
        })
        # Keep the list endpoint responsive; AI reasoning remains available
        # through the dedicated reasoning endpoint for selected alerts.
        result[-1]["reasoning"] = explain_alert(result[-1], use_llm=False)
        result[-1]["reasoning_mode"] = result[-1]["reasoning"]["mode"]
    return result


def get_alert_by_id(data_dir: str, alert_id: str) -> dict[str, Any] | None:
    """Retrieve a single high-risk alert by ID, with persisted status overlay."""
    for alert in alerts_list(data_dir):
        if alert["id"] == alert_id:
            return alert
    return None