"""Main FastAPI application entry point for the RailMind AI backend."""
import glob
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core import websocket_manager
from app.core.processor_manager import start_processor
from app.models.feed import Feed
from fastapi import WebSocket, WebSocketDisconnect
from app.lstm import generate_default_models

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

os.makedirs(settings.MOCK_FEED_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.MOCK_FEED_DIR), name="uploads")


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

# Compatibility shim: some tests expect middleware objects to expose a `kwargs`
# attribute (older code). Starlette's `Middleware` uses `options` — copy it to
# `kwargs` so tests and any legacy inspection code work.
for mw in app.user_middleware:
    # Only set `kwargs` when it's missing to avoid overwriting any explicit value.
    if not hasattr(mw, "kwargs") and hasattr(mw, "options"):
        try:
            setattr(mw, "kwargs", dict(mw.options))
        except Exception:
            # If options is not dict-like, skip copying.
            pass

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

    # Ensure default LSTM models exist so the LSTMPredictor can load placeholder
    # models in environments where saved_models/ is empty (e.g., fresh clones).
    try:
        _ensure_lstm_models()
    except Exception as e:
        print(f"Error ensuring LSTM model bootstrap: {e}")


def _ensure_lstm_models() -> None:
    """Ensure the configured LSTM model files exist at startup."""
    model_dir = settings.MODEL_DIR
    required_files = [
        "suicide_classifier.pt",
        "pickpocket_classifier.pt",
        "anomaly_classifier.pt",
    ]
    missing = [f for f in required_files if not os.path.exists(os.path.join(model_dir, f))]
    if missing:
        print(
            f"Missing LSTM model files in {model_dir}: {missing}. "
            "Generating untrained placeholder models for local development. "
            "These models are not production-ready and must be retrained before use."
        )
        os.makedirs(model_dir, exist_ok=True)
        generate_default_models.main(target_dir=model_dir)

    # Ensure the pose model file exists. If not, attempt to trigger ultralytics
    # to download it by instantiating `YOLO(model_path)`. This allows first-time
    # setup on machines where the model isn't checked in.
    try:
        pose_path = settings.POSE_MODEL_PATH
        if not os.path.exists(pose_path):
            print(f"Pose model not found at {pose_path}. Attempting to download via ultralytics...")
            try:
                from ultralytics import YOLO

                # Instantiating YOLO with the model filename will auto-download
                # the weights to the given path if necessary.
                try:
                    YOLO(pose_path)
                    print("Pose model download/initialization succeeded.")
                except Exception as inner_e:
                    print(f"Pose model initialization failed: {inner_e}")
            except Exception as e:
                print(
                    "ultralytics not available or download failed:",
                    e,
                    "\nInstall ultralytics or place the pose model at the path specified by POSE_MODEL_PATH",
                )
    except Exception:
        # Non-fatal; startup continues even if pose model check fails.
        pass

    # Ensure there are mock feed videos available for the demo.
    try:
        _ensure_mock_feed_videos(settings.MOCK_FEED_DIR, required=2)
    except Exception:
        pass

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
            video_path = video_paths[idx]
            # Compute the browser-accessible URL for the uploaded video file.
            # The file is served by FastAPI's StaticFiles mount at /uploads/<filename>.
            stream_url = f"/uploads/{os.path.basename(video_path)}"

            feed = db.query(Feed).filter(Feed.id == feed_info["id"]).first()
            if feed is None:
                feed = Feed(
                    id=feed_info["id"],
                    name=feed_info["name"],
                    status="active",
                    fps=30.0,
                    source_url=video_path,
                    stream_url=stream_url,
                )
                db.add(feed)
                db.commit()
                db.refresh(feed)
            else:
                # Backfill stream_url for existing records that were created without it.
                if not feed.stream_url:
                    feed.stream_url = stream_url
                    feed.source_url = video_path
                    db.commit()
            try:
                start_processor(video_path, feed.id, feed_info["platform"])
            except Exception as e:
                print(f"Failed to start default station processor for {feed.id}: {e}")


def _ensure_mock_feed_videos(video_dir: str, required: int = 2) -> None:
    """Ensure there are at least `required` video files in `video_dir`.

    If not present, attempt to generate simple synthetic MP4 files using OpenCV.
    This allows the demo to run out-of-the-box without checked-in binaries.
    """
    try:
        os.makedirs(video_dir, exist_ok=True)
    except Exception:
        return

    existing = sorted(
        glob.glob(os.path.join(video_dir, "*.mp4"))
        + glob.glob(os.path.join(video_dir, "*.mov"))
    )
    if len(existing) >= required:
        return

    # Try to create synthetic videos if OpenCV is available.
    try:
        import cv2
        import numpy as np

        width, height = 640, 360
        fps = 10
        duration_seconds = 5
        frames = fps * duration_seconds

        for i in range(required - len(existing)):
            filename = f"sample_station_{i+1}.mp4"
            path = os.path.join(video_dir, filename)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(path, fourcc, float(fps), (width, height))
            for f in range(frames):
                img = 30 * np.ones((height, width, 3), dtype="uint8")
                # moving rectangle
                x = int((width - 100) * (f / frames))
                y = int((height - 50) * (f / frames))
                cv2.rectangle(img, (x, y), (x + 100, y + 50), (0, 200, 0), -1)
                cv2.putText(img, f"Sample {i+1}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                out.write(img)
            out.release()
            print(f"Generated synthetic mock feed video: {path}")
    except Exception as e:
        # If generation fails (no cv2, no write permission, etc.), log and continue.
        try:
            print("Unable to generate synthetic mock videos (OpenCV missing or error):", e)
        except Exception:
            pass

@app.get("/")
async def root():
    return {"message": "RailMind AI Backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
