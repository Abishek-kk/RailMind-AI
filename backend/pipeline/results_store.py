"""
results_store.py

Minimal persistence layer for processed video results.

There's no database in this stack yet, so results are kept in a single
JSON file on disk: backend/data/pipeline_video_data/results_store.json

Each entry:
    {
        "video_id": str,
        "feed_id": str,
        "feed_name": str,
        "camera_id": str,           # same as feed_id for now, one feed = one camera
        "source_filename": str,
        "processed_at": iso8601 str,
        "annotated_video_path": str,        # relative, for building a URL
        "tracks": { track_id(str): {...same shape process_video returns...} },
    }

This is intentionally simple -- swap for a real DB later without
changing the endpoint logic in main.py, since everything reads through
the functions below.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

_LOCK = threading.Lock()


def _store_path(data_dir: str) -> str:
    return os.path.join(data_dir, "results_store.json")


def _load_all_unlocked(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def load_all(data_dir: str) -> list[dict[str, Any]]:
    path = _store_path(data_dir)
    with _LOCK:
        return _load_all_unlocked(path)


def save_result(
    data_dir: str,
    *,
    video_id: str,
    feed_id: str,
    feed_name: str,
    camera_id: str,
    source_filename: str,
    annotated_video_path: str,
    tracks: dict[Any, dict[str, Any]],
) -> dict[str, Any]:
    """Appends (or replaces, if feed_id already exists) one video's result."""
    os.makedirs(data_dir, exist_ok=True)
    path = _store_path(data_dir)

    entry = {
        "video_id": video_id,
        "feed_id": feed_id,
        "feed_name": feed_name,
        "camera_id": camera_id,
        "source_filename": source_filename,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "annotated_video_path": annotated_video_path,
        # track_id keys come back as ints/np ints from the pipeline;
        # normalize to str for stable JSON round-tripping
        "tracks": {str(k): v for k, v in tracks.items()},
    }

    with _LOCK:
        all_results = _load_all_unlocked(path)
        all_results = [r for r in all_results if r["feed_id"] != feed_id]
        all_results.append(entry)
        with open(path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)

    return entry


def get_by_feed_id(data_dir: str, feed_id: str) -> dict[str, Any] | None:
    for entry in load_all(data_dir):
        if entry["feed_id"] == feed_id:
            return entry
    return None