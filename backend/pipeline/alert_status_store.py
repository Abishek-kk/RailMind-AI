"""
alert_status_store.py

Minimal persistence layer for alert status and operator assignments.

Stores alert status ("active"/"acknowledged"/"resolved") and operator_assigned
per alert_id in a JSON file: backend/data/pipeline_video_data/alert_status_store.json

Each entry:
    {
        "alert_id": str,            # e.g., "feed-123-track-456"
        "status": str,              # "active", "acknowledged", or "resolved"
        "operator_assigned": str | null,  # operator ID or None
        "updated_at": iso8601 str,  # timestamp of last update
    }

This allows aggregation.alerts_list() to overlay persisted state onto derived alerts
without storing redundant copies of the full alert data.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

_LOCK = threading.Lock()


def _store_path(data_dir: str) -> str:
    return os.path.join(data_dir, "alert_status_store.json")


def _load_all_unlocked(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def load_all(data_dir: str) -> list[dict[str, Any]]:
    """Load all alert status records."""
    path = _store_path(data_dir)
    with _LOCK:
        return _load_all_unlocked(path)


def get_status(data_dir: str, alert_id: str) -> dict[str, Any] | None:
    """Get status and operator assignment for a specific alert_id."""
    for record in load_all(data_dir):
        if record["alert_id"] == alert_id:
            return record
    return None


def update_status(
    data_dir: str,
    alert_id: str,
    status: str,
    operator_assigned: str | None = None,
) -> dict[str, Any]:
    """Update or create an alert status record."""
    os.makedirs(data_dir, exist_ok=True)
    path = _store_path(data_dir)

    record = {
        "alert_id": alert_id,
        "status": status,
        "operator_assigned": operator_assigned,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    with _LOCK:
        all_records = _load_all_unlocked(path)
        existing = next((r for r in all_records if r["alert_id"] == alert_id), {})
        # Remove existing record with this alert_id if present
        all_records = [r for r in all_records if r["alert_id"] != alert_id]
        # Append new/updated record
        record = {
            **existing,
            **record,
            "operator_assigned": operator_assigned
            if operator_assigned is not None
            else existing.get("operator_assigned"),
        }
        all_records.append(record)
        with open(path, "w") as f:
            json.dump(all_records, f, indent=2, default=str)

    return record


def escalate(
    data_dir: str,
    alert_id: str,
    handling_level: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Persist a handling-level escalation without changing alert status."""
    os.makedirs(data_dir, exist_ok=True)
    path = _store_path(data_dir)

    with _LOCK:
        all_records = _load_all_unlocked(path)
        existing = next((r for r in all_records if r["alert_id"] == alert_id), {})
        record = {
            **existing,
            "alert_id": alert_id,
            "status": existing.get("status", "active"),
            "operator_assigned": existing.get("operator_assigned"),
            "handling_level": handling_level,
            "escalation_reason": reason,
            "escalated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        all_records = [r for r in all_records if r["alert_id"] != alert_id]
        all_records.append(record)
        with open(path, "w") as f:
            json.dump(all_records, f, indent=2, default=str)

    return record
