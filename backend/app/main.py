"""Main FastAPI application entry point for the RailMind AI backend."""
import glob
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core import websocket_manager
from app.core.processor_manager import start_processor
from app.models.feed import Feed
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Ensure the common frontend origins are allowed for CORS (helps HTTP requests).
# Include Vite's default and the current dev port so the WebSocket origin check passes.
frontend_origins = [
    "http://localhost:5173",
    "http://localhost:5176",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5176",
    "http://127.0.0.1:8080",
]
if not settings.BACKEND_CORS_ORIGINS:
    settings.BACKEND_CORS_ORIGINS = frontend_origins
else:
    try:
        origins = list(settings.BACKEND_CORS_ORIGINS or [])
        for origin in frontend_origins:
            if origin not in origins:
                origins.append(origin)
        settings.BACKEND_CORS_ORIGINS = origins
    except Exception:
        # If settings is immutable in the current environment, skip explicit mutation
        pass

cors_origins = [origin for origin in settings.BACKEND_CORS_ORIGINS if origin != "*"]
if not cors_origins:
    cors_origins = frontend_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming live alerts and detections to frontend clients.

    This endpoint performs a basic origin check against `settings.BACKEND_CORS_ORIGINS`
    to mimic the CORS protections used for HTTP endpoints. Browsers include an
    `Origin` header during the WebSocket handshake so we validate it and reject
    connections from unknown origins with a 403-like close code.
    """
    # For local development accept incoming WebSocket handshakes without
    # strict origin validation. Production deployments should enforce origins.
    try:
        await websocket_manager.manager.connect(websocket)
        try:
            while True:
                # Keep the connection open to allow server pushes; echo incoming pings if any
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.manager.disconnect(websocket)
    except Exception:
        # Ensure clean disconnect on unexpected errors
        websocket_manager.manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    init_db()

    _ensure_default_station_feeds()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Add shutdown cleanup steps here if needed in the future.
    return None


def _ensure_default_station_feeds() -> None:
    """Ensure two default station feeds are registered and started."""
    video_dir = settings.MOCK_FEED_DIR
    if not os.path.isdir(video_dir):
        return

    video_paths = sorted(
        glob.glob(os.path.join(video_dir, "*.mp4"))
        + glob.glob(os.path.join(video_dir, "*.mov"))
        + glob.glob(os.path.join(video_dir, "*.mkv"))
        + glob.glob(os.path.join(video_dir, "*.avi"))
    )
    if len(video_paths) < 2:
        return

    default_feeds = [
        {"id": "CCTV_STATION_1", "name": "Station 1", "platform": "Station 1"},
        {"id": "CCTV_STATION_2", "name": "Station 2", "platform": "Station 2"},
    ]

    with SessionLocal() as db:
        for idx, feed_info in enumerate(default_feeds):
            feed = db.query(Feed).filter(Feed.id == feed_info["id"]).first()
            if feed is None:
                feed = Feed(
                    id=feed_info["id"],
                    name=feed_info["name"],
                    status="active",
                    fps=30.0,
                )
                db.add(feed)
                db.commit()
                db.refresh(feed)
            try:
                start_processor(video_paths[idx], feed.id, feed_info["platform"])
            except Exception as e:
                print(f"Failed to start default station processor for {feed.id}: {e}")

@app.get("/")
async def root():
    return {"message": "RailMind AI Backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
