from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Body, BackgroundTasks, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader

load_dotenv()

# Load API key from environment for securing all /api/* and /ws/alerts routes
RAILMIND_API_KEY = os.getenv("RAILMIND_API_KEY", "change-this-admin-api-key")

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
from pipeline.alert_reasoning import explain_alert  # noqa: E402
from pipeline import alert_status_store  # noqa: E402
from pipeline import results_store as store  # noqa: E402
from pipeline.pipeline import process_video  # noqa: E402


# ---------------------------------------------------------------------
# API Key Verification
# ---------------------------------------------------------------------
def verify_api_key_http(api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False))) -> str:
    """
    FastAPI Security dependency to verify X-API-Key header against RAILMIND_API_KEY.
    Applied to all /api/* routes. Raises HTTPException 403 if key is missing or invalid.
    """
    if api_key is None or api_key.strip() == "":
        raise HTTPException(
            status_code=403,
            detail="Missing X-API-Key header",
        )
    if api_key != RAILMIND_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid X-API-Key",
        )
    return api_key


# Connection manager for real-time alert broadcasting
class AlertConnectionManager:
    """Manages WebSocket connections for real-time alert streaming."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection failed, mark for removal
                disconnected.append(connection)
        
        # Clean up failed connections
        for connection in disconnected:
            self.disconnect(connection)


alert_manager = AlertConnectionManager()


app = FastAPI(title="RailMind AI", version="1.0.0")
app.mount("/uploads", StaticFiles(directory=str(VIDEO_FEEDS_DIR)), name="uploads")
app.mount("/processed", StaticFiles(directory=str(PIPELINE_DATA_DIR)), name="processed")


def _load_cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:3000,http://127.0.0.1:3000",
    )
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
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):(5173|5174|3000)(?::\d+)?",
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
def health(api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    return {"status": "ok", "service": "railmind-api"}


# ---------------------------------------------------------------------
# Dashboard endpoints -- now backed by aggregation.py over real results
# ---------------------------------------------------------------------

@app.get("/api/dashboard/stats")
def dashboard_stats(api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    return aggregation.dashboard_stats(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/incidents-by-cctv")
def incidents_by_cctv(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    return aggregation.incidents_by_cctv(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/trend")
def dashboard_trend(days: int = 7, api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    return aggregation.trend(str(PIPELINE_DATA_DIR), days=days)


@app.get("/api/dashboard/risk-distribution")
def risk_distribution(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    return aggregation.risk_distribution(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/peak-hours")
def peak_hours(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    return aggregation.peak_hours(str(PIPELINE_DATA_DIR))


@app.get("/api/dashboard/heatmap")
def heatmap(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    # No zone-level (North/South/East) subdivision exists in the pipeline's
    # output today -- it only has a single track_zone + platform_zone per
    # camera, not named sub-zones. Returning per-camera intrusion counts
    # instead of fabricating zone names that don't correspond to anything
    # actually calibrated.
    counts = aggregation.incidents_by_cctv(str(PIPELINE_DATA_DIR))
    return [{"platform": c["camera_id"], "zone": "track_zone", "intensity": c["incidents"]} for c in counts]


@app.get("/api/dashboard/cctv-summary")
def cctv_summary(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    return aggregation.cctv_summary(str(PIPELINE_DATA_DIR))


# ---------------------------------------------------------------------
# Incidents / Alerts -- real, derived from stored pipeline results
# ---------------------------------------------------------------------

@app.get("/api/incidents")
def incidents(status: str | None = None, limit: int | None = None, api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    """Get incidents with optional filtering by status and limiting by count.
    
    Query parameters:
    - status: Filter by status (e.g., "active", "acknowledged", "resolved")
    - limit: Maximum number of most recent incidents to return
    """
    result = aggregation.incidents_list(str(PIPELINE_DATA_DIR))
    
    # Filter by status if provided
    if status:
        result = [inc for inc in result if inc.get("status") == status]
    
    # Sort by timestamp descending (most recent first)
    result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Limit the number of results if provided
    if limit is not None and limit > 0:
        result = result[:limit]
    
    return result


@app.get("/api/alerts")
def alerts(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
    return aggregation.alerts_list(str(PIPELINE_DATA_DIR))


@app.post("/api/alerts/reasoning")
def explain_alert_input(body: dict[str, Any] = Body(...), api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    return explain_alert(body)


@app.get("/api/alerts/{alert_id}/reasoning")
def alert_reasoning(alert_id: str, api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    alert = aggregation.get_alert_by_id(str(PIPELINE_DATA_DIR), alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return explain_alert(alert)


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, operator_id: str | None = None, api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    # Update persisted alert status with operator_id from query parameter
    alert_status_store.update_status(
        str(PIPELINE_DATA_DIR),
        alert_id,
        status="acknowledged",
        operator_assigned=operator_id,
    )
    # Return the full alert record
    alert = aggregation.get_alert_by_id(str(PIPELINE_DATA_DIR), alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.patch("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    # Update persisted alert status
    alert_status_store.update_status(
        str(PIPELINE_DATA_DIR),
        alert_id,
        status="resolved",
    )
    # Return the full alert record
    alert = aggregation.get_alert_by_id(str(PIPELINE_DATA_DIR), alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.post("/api/alerts/{alert_id}/assign")
def assign_alert(alert_id: str, body: dict[str, Any] = Body(...), api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    assignee = body.get("assignee")
    # Update persisted alert status with assignee as operator_assigned
    alert_status_store.update_status(
        str(PIPELINE_DATA_DIR),
        alert_id,
        status="active",
        operator_assigned=assignee,
    )
    # Return the full alert record
    alert = aggregation.get_alert_by_id(str(PIPELINE_DATA_DIR), alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


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

    feed["track_count"] = len(result.get("tracks") or {})
    return feed


@app.get("/api/feeds")
def feeds(api_key: str = Depends(verify_api_key_http)) -> list[dict[str, Any]]:
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
def create_feed(payload: dict[str, Any], api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
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


def _process_and_broadcast_alerts(
    video_path: str, feed_id: str, feed_name: str, safe_name: str
) -> None:
    """Process video and broadcast any high-risk alerts to connected WebSocket clients."""
    import asyncio
    
    try:
        pipeline_result = process_video(
            video_path, conf_threshold=0.35, save_annotated_frames=True
        )

        from pipeline.pipeline import _video_paths  # local import: internal helper

        paths = _video_paths(video_path)
        annotated_rel_path = os.path.relpath(paths["annotated_video_path"], PIPELINE_DATA_DIR)
        annotated_rel_path = annotated_rel_path.replace("\\", "/")

        store.save_result(
            str(PIPELINE_DATA_DIR),
            video_id=paths["video_id"],
            feed_id=feed_id,
            feed_name=feed_name,
            camera_id=feed_id,
            source_filename=safe_name,
            annotated_video_path=annotated_rel_path,
            tracks=pipeline_result,
        )

        # Broadcast high-risk alerts to all connected WebSocket clients
        alerts = aggregation.alerts_list(str(PIPELINE_DATA_DIR))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            for alert in alerts:
                loop.run_until_complete(
                    alert_manager.broadcast({
                        "type": "new_alert",
                        "data": alert,
                    })
                )
        finally:
            loop.close()
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")


@app.post("/api/feeds/upload")
async def upload_feed(
    file: UploadFile = File(...),
    feed_id: str = Form(default=""),
    name: str = Form(default=""),
    api_key: str = Depends(verify_api_key_http),
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

    # Run video processing in background to avoid blocking the upload response
    background_task = BackgroundTasks()
    background_task.add_task(
        _process_and_broadcast_alerts,
        str(destination),
        feed_key,
        feed_name,
        safe_name,
    )

    return JSONResponse(
        {
            "id": feed_key,
            "status": "processing",
            "msg": "Video uploaded and queued for processing. Alerts will be streamed in real-time.",
        },
        background=background_task,
    )


@app.get("/api/feeds/{feed_id}/result")
def feed_result(feed_id: str, api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    """Full stored pipeline result for one feed: per-track activity + annotated video path."""
    entry = store.get_by_feed_id(str(PIPELINE_DATA_DIR), feed_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No pipeline result found for feed_id={feed_id}")
    entry = dict(entry)
    entry["annotated_video_path"] = entry["annotated_video_path"].replace("\\", "/")
    entry["annotated_video_url"] = f"/processed/{entry['annotated_video_path']}"
    return entry


@app.delete("/api/feeds/{feed_id}")
def delete_feed(feed_id: str, api_key: str = Depends(verify_api_key_http)) -> dict[str, Any]:
    FEEDS[:] = [item for item in FEEDS if item.get("id") != feed_id]
    store.delete_by_feed_id(str(PIPELINE_DATA_DIR), feed_id)
    return {"status": "deleted", "feed_id": feed_id}


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket) -> None:
    """Real-time alert stream. Broadcasts high-risk incidents as they're detected.
    
    Requires api_key query parameter matching RAILMIND_API_KEY environment variable.
    Closes with code 1008 (policy violation) if authentication fails.
    """
    # Extract and validate API key from query parameters before accepting connection
    api_key = websocket.query_params.get("api_key")
    if api_key is None or api_key.strip() == "" or api_key != RAILMIND_API_KEY:
        # Close with code 1008 (policy violation) if key is missing or invalid
        # Frontend's useWebSocket.ts handles 1008 specially
        await websocket.close(code=1008, reason="Invalid or missing API key")
        return
    
    await alert_manager.connect(websocket)
    try:
        # Keep connection alive; messages are pushed from process_video
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})