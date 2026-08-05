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

BASE_DIR = "backend"
VIDEO_FEEDS_DIR = BASE_DIR / "data" / "input_video_Data"

app = FastAPI(title="RailMind AI", version="1.0.0")
app.mount("/uploads", StaticFiles(directory=str(VIDEO_FEEDS_DIR)), name="uploads")


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


DASHBOARD_STATS = {
    "total_incidents": 18,
    "active_alerts": 4,
    "security_threats": 2,
    "suicide_mitigations": 3,
    "theft_preventions": 5,
    "system_status": "Operational",
}

INCIDENTS_BY_CCTV = [
    {"camera_id": "CCTV-1", "incidents": 7},
    {"camera_id": "CCTV-2", "incidents": 5},
    {"camera_id": "CCTV-3", "incidents": 3},
    {"camera_id": "CCTV-4", "incidents": 3},
]

TREND = [
    {"date": "2026-07-28", "Suicide Risk": 1, "Pickpocketing": 2, "Loitering": 3},
    {"date": "2026-07-29", "Suicide Risk": 2, "Pickpocketing": 1, "Loitering": 4},
    {"date": "2026-07-30", "Suicide Risk": 1, "Pickpocketing": 3, "Loitering": 2},
    {"date": "2026-07-31", "Suicide Risk": 3, "Pickpocketing": 2, "Loitering": 1},
]

RISK_DISTRIBUTION = [
    {"name": "Suicide Risk Detection", "value": 6},
    {"name": "Pickpocketing Actions", "value": 4},
    {"name": "Loitering / Trespass", "value": 5},
    {"name": "General Anomalies", "value": 3},
]

PEAK_HOURS = [
    {"hour": "08:00", "incidents": 2},
    {"hour": "10:00", "incidents": 4},
    {"hour": "14:00", "incidents": 6},
    {"hour": "18:00", "incidents": 5},
]

HEATMAP = [
    {"platform": "Platform A", "zone": "North", "intensity": 3},
    {"platform": "Platform A", "zone": "South", "intensity": 7},
    {"platform": "Platform B", "zone": "East", "intensity": 4},
]

CCTV_SUMMARY = [
    {
        "camera_id": "CCTV-1",
        "location": "North Entrance",
        "status": "online",
        "total_incidents": 6,
        "active_alerts": 2,
        "current_risk_level": "High",
        "last_incident": "2026-08-04T14:20:00Z",
    },
    {
        "camera_id": "CCTV-2",
        "location": "Main Concourse",
        "status": "online",
        "total_incidents": 5,
        "active_alerts": 1,
        "current_risk_level": "Medium",
        "last_incident": "2026-08-04T14:05:00Z",
    },
]

ALERTS = [
    {
        "id": 1,
        "person_id": "P-101",
        "camera_id": "CCTV-1",
        "platform": "Platform A",
        "incident_type": "Suicide Risk Detection",
        "risk_score": 88,
        "risk_level": "High",
        "status": "active",
        "timestamp": "2026-08-04T14:20:00Z",
        "operator_assigned": None,
        "reasoning_mode": "rule-based",
    },
    {
        "id": 2,
        "person_id": "P-205",
        "camera_id": "CCTV-2",
        "platform": "Platform B",
        "incident_type": "Pickpocketing Actions",
        "risk_score": 71,
        "risk_level": "Medium",
        "status": "active",
        "timestamp": "2026-08-04T14:05:00Z",
        "operator_assigned": "Ops-1",
        "reasoning_mode": "rule-based",
    },
]

FEEDS = [
    {
        "id": "feed-1",
        "name": "North Entrance",
        "status": "active",
        "fps": 25,
        "stream_url": "/uploads/Woman Attempts To Climb The Roof Of A Crowded Train, Fails Miserably _ #viral _ #viralvideo_Woman Attempts To Climb The Roof Of A Crowded Train, Fails Miserably _ #viral _ #viralvideo.mp4",
    },
    {
        "id": "feed-2",
        "name": "Main Concourse",
        "status": "active",
        "fps": 24,
        "stream_url": "/uploads/AdobeStock_206827806_Video_HD_Preview_AdobeStock_206827806_Video_HD_Preview.mov",
    },
]


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "railmind-api"}


@app.get("/api/dashboard/stats")
def dashboard_stats() -> dict[str, Any]:
    return DASHBOARD_STATS


@app.get("/api/dashboard/incidents-by-cctv")
def incidents_by_cctv() -> list[dict[str, Any]]:
    return INCIDENTS_BY_CCTV


@app.get("/api/dashboard/trend")
def dashboard_trend(days: int = 7) -> list[dict[str, Any]]:
    return TREND[: max(1, min(days, len(TREND)))]


@app.get("/api/dashboard/risk-distribution")
def risk_distribution() -> list[dict[str, Any]]:
    return RISK_DISTRIBUTION


@app.get("/api/dashboard/peak-hours")
def peak_hours() -> list[dict[str, Any]]:
    return PEAK_HOURS


@app.get("/api/dashboard/heatmap")
def heatmap() -> list[dict[str, Any]]:
    return HEATMAP


@app.get("/api/dashboard/cctv-summary")
def cctv_summary() -> list[dict[str, Any]]:
    return CCTV_SUMMARY


@app.get("/api/incidents")
def incidents() -> list[dict[str, Any]]:
    return [
        {
            "id": 101,
            "camera_id": "CCTV-1",
            "platform": "Platform A",
            "incident_type": "Suicide Risk Detection",
            "risk_score": 84,
            "risk_level": "High",
            "status": "active",
            "timestamp": "2026-08-04T14:20:00Z",
        },
        {
            "id": 102,
            "camera_id": "CCTV-2",
            "platform": "Platform B",
            "incident_type": "Pickpocketing Actions",
            "risk_score": 67,
            "risk_level": "Medium",
            "status": "active",
            "timestamp": "2026-08-04T14:05:00Z",
        },
    ]


@app.get("/api/alerts")
def alerts() -> list[dict[str, Any]]:
    return ALERTS


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int) -> dict[str, str]:
    return {"status": "acknowledged", "alert_id": str(alert_id)}


@app.patch("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int) -> dict[str, str]:
    return {"status": "resolved", "alert_id": str(alert_id)}


@app.post("/api/alerts/{alert_id}/assign")
def assign_alert(alert_id: int) -> dict[str, str]:
    return {"status": "assigned", "alert_id": str(alert_id)}


@app.get("/api/feeds")
def feeds() -> list[dict[str, Any]]:
    return FEEDS


@app.post("/api/feeds")
def create_feed(payload: dict[str, Any]) -> dict[str, Any]:
    feed_id = payload.get("id", "feed-new")
    FEEDS.append(
        {
            "id": feed_id,
            "name": payload.get("name", "New Feed"),
            "status": "active",
            "fps": 25,
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
    VIDEO_FEEDS_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = file.filename or "uploaded-video"
    destination = VIDEO_FEEDS_DIR / safe_name
    contents = await file.read()
    destination.write_bytes(contents)

    feed_key = feed_id or f"feed-{len(FEEDS) + 1}"
    feed_name = name or safe_name
    FEEDS.append(
        {
            "id": feed_key,
            "name": feed_name,
            "status": "active",
            "fps": 25,
            "stream_url": f"/uploads/{safe_name}",
        }
    )

    try:
        from pipeline.pipeline import process_video

        pipeline_result = process_video(str(destination), conf_threshold=0.35, save_annotated_frames=True)
        return {
            "id": feed_key,
            "status": "uploaded",
            "msg": "Upload accepted and pipeline processed",
            "track_count": len(pipeline_result),
        }
    except Exception as exc:
        return {
            "id": feed_key,
            "status": "uploaded",
            "msg": f"Upload saved; pipeline skipped: {exc}",
            "saved_path": str(destination),
        }


@app.delete("/api/feeds/{feed_id}")
def delete_feed(feed_id: str) -> dict[str, Any]:
    for item in FEEDS:
        if item["id"] == feed_id:
            FEEDS.remove(item)
            break
    return {"status": "deleted", "feed_id": feed_id}


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket) -> None:
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
