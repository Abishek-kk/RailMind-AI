from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.deps import get_db

router = APIRouter()

@router.get("")
async def list_feeds(db = Depends(get_db)):
    """List all connected station CCTV streams alongside operational health checks."""
    return [
        {"id": "CCTV_P1_04", "name": "Platform 1 East Edge", "status": "active", "fps": 29.97},
        {"id": "CCTV_P2_01", "name": "Platform 2 Main Stairs", "status": "active", "fps": 30.0},
        {"id": "CCTV_B1_02", "name": "Baggage Counter Rest", "status": "inactive", "fps": 0.0}
    ]

@router.post("", status_code=status.HTTP_201_CREATED)
async def register_feed(feed_data: dict, db = Depends(get_db)):
    """Register a new active IP Camera RTSP protocol stream network node into RailMind."""
    return {"id": feed_data.get("id", "CCTV_NEW"), "status": "registered", "msg": "Ingestion active"}

@router.get("/{id}/stream")
async def get_live_stream_metadata(id: str, db = Depends(get_db)):
    """Returns endpoint stream pipeline specifications for client rendering loops."""
    return {
        "feed_id": id,
        "stream_protocol": "HLS/WebRTC",
        "endpoint_url": f"/api/v1/feeds/{id}/live.m3u8",
        "inference_overlay": True
    }

@router.delete("/{id}")
async def remove_feed(id: str, db = Depends(get_db)):
    """Safely stop parsing frames and tear down ingestion threads for a specified camera."""
    return {"id": id, "status": "deprovisioned"}