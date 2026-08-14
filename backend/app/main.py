from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
# This file lives at backend/app/main.py, so backend/ is one level up.
# Using Path objects throughout (not strings) so the `/` joins below
# actually work -- mixing str and Path was the original bug here.
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent  # backend/

VIDEO_FEEDS_DIR = BASE_DIR / "data" / "input_video_data"
PIPELINE_DATA_DIR = BASE_DIR / "data" / "pipeline_video_data"

VIDEO_FEEDS_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Point the pipeline's own working directory (frames/annotated/zones/events
# per video) at backend/data/pipeline_video_data instead of wherever the
# process happens to be launched from.
os.environ.setdefault("PIPELINE_WORK_ROOT", str(PIPELINE_DATA_DIR))

# `backend/` needs to be importable as a package root so `pipeline.pipeline`
# and `pipeline.results_store` resolve regardless of the CWD uvicorn was
# started from.
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from pipeline import aggregation  # noqa: E402
from pipeline import results_store as store  # noqa: E402
from pipeline.pipeline import process_video  # noqa: E402


app = FastAPI(title="RailMind AI", version="1.0.0")
app.mount("/uploads", StaticFiles(directory=str(VIDEO_FEEDS_DIR)), name="uploads")
app.mount("/processed", StaticFiles(directory=str(PIPELINE_DATA_DIR)), name="processed")


def _load_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(origin).strip().strip('"\'') for origin in parsed if str(origin).strip()]
    except Exception:
        pass

    return [
        origin.strip().strip('"\'')
        for origin in raw.split(",")
        if origin.strip()
    ]


cors_origins = _load_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# In-memory feed registry
# ---------------------------------------------------------------------
# Feeds themselves (name, source video, status) aren't produced by the
# pipeline, so they still live in memory here -- but every dashboard/
# incident/alert endpoint below reads real data from results_store.py,
# populated by actually running the pipeline on upload.
FEEDS: list[dict[str, Any]] = []


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "railmind-api"}


# ---------------------------------------------------------------------
# Dashboard endpoints -- now backed by aggregation.py over real results
# ---------------------------------------------------------------------

@app.get("/api/dashboard/stats")
def dashboard_stats() -> dict[str, Any]:
    return aggregation.dashboard_stats(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/incidents-by-cctv")
def incidents_by_cctv() -> list[dict[str, Any]]:
    return aggregation.incidents_by_cctv(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/trend")
def dashboard_trend(days: int = 7) -> list[dict[str, Any]]:
    return aggregation.trend(str(PIPELINE_DATA_DIR), days=days)


@app.get("/api/dashboard/risk-distribution")
def risk_distribution() -> list[dict[str, Any]]:
    return aggregation.risk_distribution(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/peak-hours")
def peak_hours() -> list[dict[str, Any]]:
    return aggregation.peak_hours(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/heatmap")
def heatmap() -> list[dict[str, Any]]:
    # No zone-level (North/South/East) subdivision exists in the pipeline's
    # output today -- it only has a single track_zone + platform_zone per
    # camera, not named sub-zones. Returning per-camera intrusion counts
    # instead of fabricating zone names that don't correspond to anything
    # actually calibrated.
    counts = aggregation.incidents_by_cctv(str(PIPELINE_DATA_DIR))
    return [{"platform": c["camera_id"], "zone": "track_zone", "intensity": c["incidents"]} for c in counts]


@app.get("/api/dashboard/cctv-summary")
def cctv_summary() -> list[dict[str, Any]]:
    return aggregation.cctv_summary(str(PIPELINE_DATA_DIR))


# ---------------------------------------------------------------------
# Incidents / Alerts -- real, derived from stored pipeline results
# ---------------------------------------------------------------------

@app.get("/api/incidents")
def incidents() -> list[dict[str, Any]]:
    return aggregation.incidents_list(str(PIPELINE_DATA_DIR))


@app.get("/api/alerts")
def alerts() -> list[dict[str, Any]]:
    return aggregation.alerts_list(str(PIPELINE_DATA_DIR))


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str) -> dict[str, str]:
    # Acknowledge/assign/resolve are operator actions with no persisted
    # state of their own yet (there's no alerts table -- alerts are
    # derived live from results_store each request). Wire these to a
    # real status store if/when you need acknowledgement to persist.
    return {"status": "acknowledged", "alert_id": alert_id}


@app.patch("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str) -> dict[str, str]:
    return {"status": "resolved", "alert_id": alert_id}


@app.post("/api/alerts/{alert_id}/assign")
def assign_alert(alert_id: str) -> dict[str, str]:
    return {"status": "assigned", "alert_id": alert_id}


# ---------------------------------------------------------------------
# Feeds
# ---------------------------------------------------------------------

def _enrich_feed_with_processed_video(feed: dict[str, Any]) -> dict[str, Any]:
    feed = dict(feed)
    feed_id = str(feed.get("id"))
    if not feed_id:
        return feed

    result = store.get_by_feed_id(str(PIPELINE_DATA_DIR), feed_id)
    if result is None:
        return feed

    annotated_path = str(result.get("annotated_video_path", "")).replace("\\", "/")
    if annotated_path:
        feed["stream_url"] = f"/processed/{annotated_path}"
        feed["annotated_video_url"] = f"/processed/{annotated_path}"
    return feed


@app.get("/api/feeds")
def feeds() -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for raw_feed in FEEDS:
        feed = _enrich_feed_with_processed_video(raw_feed)
        feed_id = str(feed.get("id"))
        if feed_id and feed_id not in seen_ids:
            seen_ids.add(feed_id)
            enriched.append(feed)

    for result in store.load_all(str(PIPELINE_DATA_DIR)):
        feed_id = str(result.get("feed_id", ""))
        if not feed_id or feed_id in seen_ids:
            continue

        annotated_path = str(result.get("annotated_video_path", "")).replace("\\", "/")
        enriched.append(
            {
                "id": feed_id,
                "name": result.get("feed_name") or feed_id,
                "status": "active",
                "stream_url": f"/processed/{annotated_path}",
                "annotated_video_url": f"/processed/{annotated_path}",
                "track_count": len(result.get("tracks") or {}),
            }
        )
        seen_ids.add(feed_id)

    return enriched


@app.post("/api/feeds")
def create_feed(payload: dict[str, Any]) -> dict[str, Any]:
    feed_id = payload.get("id", f"feed-{len(FEEDS) + 1}")
    FEEDS.append(
        {
            "id": feed_id,
            "name": payload.get("name", "New Feed"),
            "status": "active",
            "stream_url": payload.get("source_url"),
        }
    )
    return {"id": feed_id, "status": "created", "msg": "Feed created"}


@app.post("/api/feeds/upload")
async def upload_feed(
    file: UploadFile = File(...),
    feed_id: str = Form(default=""),
    name: str = Form(default=""),
) -> dict[str, Any]:
    safe_name = file.filename or "uploaded-video"
    destination = VIDEO_FEEDS_DIR / safe_name
    contents = await file.read()
    destination.write_bytes(contents)

    feed_key = feed_id or f"feed-{len(FEEDS) + 1}"
    feed_name = name or safe_name

    feed_record = {
        "id": feed_key,
        "name": feed_name,
        "status": "active",
        "stream_url": f"/uploads/{safe_name}",
    }
    FEEDS.append(feed_record)

    try:
        pipeline_result = process_video(
            str(destination), conf_threshold=0.35, save_annotated_frames=True
        )

        # Pull the video_id + annotated video path back out so the
        # frontend can be pointed at the actual processed output.
        from pipeline.pipeline import _video_paths  # local import: internal helper

        paths = _video_paths(str(destination))
        annotated_rel_path = os.path.relpath(paths["annotated_video_path"], PIPELINE_DATA_DIR)
        annotated_rel_path = annotated_rel_path.replace("\\", "/")

        store.save_result(
            str(PIPELINE_DATA_DIR),
            video_id=paths["video_id"],
            feed_id=feed_key,
            feed_name=feed_name,
            camera_id=feed_key,
            source_filename=safe_name,
            annotated_video_path=annotated_rel_path,
            tracks=pipeline_result,
        )

        feed_record["stream_url"] = f"/processed/{annotated_rel_path}"

        return {
            "id": feed_key,
            "status": "uploaded",
            "msg": "Upload accepted and pipeline processed",
            "track_count": len(pipeline_result),
            "annotated_video_url": f"/processed/{annotated_rel_path}",
        }
    except Exception as exc:
        return {
            "id": feed_key,
            "status": "uploaded",
            "msg": f"Upload saved; pipeline skipped: {exc}",
            "saved_path": str(destination),
        }


@app.get("/api/feeds/{feed_id}/result")
def feed_result(feed_id: str) -> dict[str, Any]:
    """Full stored pipeline result for one feed: per-track activity + annotated video path."""
    entry = store.get_by_feed_id(str(PIPELINE_DATA_DIR), feed_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No pipeline result found for feed_id={feed_id}")
    entry = dict(entry)
    entry["annotated_video_path"] = entry["annotated_video_path"].replace("\\", "/")
    entry["annotated_video_url"] = f"/processed/{entry['annotated_video_path']}"
    return entry


@app.delete("/api/feeds/{feed_id}")
def delete_feed(feed_id: str) -> dict[str, Any]:
    for item in FEEDS:
        if item["id"] == feed_id:
            FEEDS.remove(item)
            break
    return {"status": "deleted", "feed_id": feed_id}


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket) -> None:
    # NOTE: this is a connectivity stub, not a live alert stream -- there's
    # no background process pushing pipeline events over this socket yet.
    # Wiring that up would mean either (a) running process_video in a
    # background task per upload and pushing new alerts as they're
    # detected, or (b) polling results_store.json for changes. Neither is
    # implemented here since it's a real design decision (queueing,
    # concurrency limits on YOLO inference, etc.), not a one-line fix.
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connected", "message": "Real-time alerts stream ready"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})