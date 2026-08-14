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

from collections import Counter
from typing import Any

from . import results_store as store

ACTIVITY_TO_INCIDENT_TYPE = {
    "IN_DANGER_ZONE": "Track Zone Intrusion",
    "PREVIOUSLY_IN_DANGER_ZONE": "Track Zone Intrusion",
    "LOITERING_ON_PLATFORM": "Loitering / Trespass",
    "ERRATIC_MOVEMENT": "General Anomalies",
}

RISK_LEVEL_BY_ACTIVITY = {
    "IN_DANGER_ZONE": "High",
    "PREVIOUSLY_IN_DANGER_ZONE": "Medium",
    "LOITERING_ON_PLATFORM": "Medium",
    "ERRATIC_MOVEMENT": "Low",
}


def _iter_incidents(data_dir: str):
    """
    Yields one dict per flagged track (NORMAL tracks are skipped --
    they're not incidents). Each dict merges the track summary with
    its video/feed context.
    """
    for entry in store.load_all(data_dir):
        for track_id, summary in entry["tracks"].items():
            activity = summary.get("activity", "NORMAL")
            if activity == "NORMAL" or activity not in ACTIVITY_TO_INCIDENT_TYPE:
                continue
            yield {
                "video_id": entry["video_id"],
                "feed_id": entry["feed_id"],
                "camera_id": entry["camera_id"],
                "processed_at": entry["processed_at"],
                "track_id": track_id,
                "incident_type": ACTIVITY_TO_INCIDENT_TYPE[activity],
                "risk_level": RISK_LEVEL_BY_ACTIVITY.get(activity, "Low"),
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
    Only dates that actually have processed videos will appear --
    no synthetic date range is invented.
    """
    by_date: dict[str, Counter] = {}
    for i in _iter_incidents(data_dir):
        date_str = i["processed_at"][:10]
        by_date.setdefault(date_str, Counter())[i["incident_type"]] += 1

    rows = []
    for date_str in sorted(by_date.keys())[-days:]:
        counter = by_date[date_str]
        rows.append({
            "date": date_str,
            "Incident Risk": counter.get("Track Zone Intrusion", 0),
            "Pickpocketing": counter.get("Loitering / Trespass", 0),
            "Loitering": counter.get("General Anomalies", 0),
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
        result.append({
            "id": f"{i['feed_id']}-{i['track_id']}",
            "camera_id": i["camera_id"],
            "incident_type": i["incident_type"],
            "risk_level": i["risk_level"],
            "status": "active",
            "timestamp": i["processed_at"],
            "track_id": i["track_id"],
            "duration_tracked_s": i.get("duration_tracked_s"),
        })
    return result


def alerts_list(data_dir: str) -> list[dict[str, Any]]:
    """High-risk incidents surfaced as alerts."""
    result = []
    for i in _iter_incidents(data_dir):
        if i["risk_level"] != "High":
            continue
        result.append({
            "id": f"{i['feed_id']}-{i['track_id']}",
            "person_id": f"P-{i['track_id']}",
            "camera_id": i["camera_id"],
            "incident_type": i["incident_type"],
            "risk_level": i["risk_level"],
            "status": "active",
            "timestamp": i["processed_at"],
            "operator_assigned": None,
        })
    return result