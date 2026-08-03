"""Main FastAPI application entry point for the RailMind AI backend."""
import os
import secrets
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core import websocket_manager
from app.core.scheduler import start_scheduler, stop_scheduler
from fastapi import WebSocket, WebSocketDisconnect

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler replacing deprecated on_event hooks.

    Performs necessary startup initialization (database and model checks).
    Shutdown cleanup can be added here in the future.
    """
    # Startup
    init_db()
    try:
        _ensure_transformer_models()
    except Exception as e:
        print(f"Error ensuring transformer model bootstrap: {e}")

    # Start background scheduler for transformer retraining
    start_scheduler()

    yield

    # Shutdown: cleanup scheduler and other resources
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

os.makedirs(settings.MOCK_FEED_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.MOCK_FEED_DIR), name="uploads")


# Ensure the common frontend origins are allowed for CORS (helps HTTP requests).
# Include Vite's default and the current dev port so the WebSocket origin check passes.
frontend_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
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

cors_origins = settings.BACKEND_CORS_ORIGINS
if isinstance(cors_origins, str):
    cors_origins = [item.strip() for item in cors_origins.split(",") if item.strip()]
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


def _is_valid_websocket_api_key(api_key: str | None) -> bool:
    """Validate WebSocket API keys using the same comparison as REST routes."""
    configured_key = settings.RAILMIND_API_KEY.strip()
    return bool(configured_key and api_key and secrets.compare_digest(api_key, configured_key))


@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming live alerts and detections to frontend clients."""
    if not _is_valid_websocket_api_key(websocket.query_params.get("api_key")):
        await websocket.close(code=1008)
        return

    try:
        await websocket_manager.manager.connect(websocket, channel="alerts")
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.manager.disconnect(websocket)
    except Exception:
        websocket_manager.manager.disconnect(websocket)


@app.websocket("/ws/feed/{camera_id}")
async def websocket_feed_endpoint(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint for streaming annotated feed data for a specific camera."""
    if not _is_valid_websocket_api_key(websocket.query_params.get("api_key")):
        await websocket.close(code=1008)
        return

    try:
        await websocket_manager.manager.connect(websocket, channel=f"feed:{camera_id}")
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.manager.disconnect(websocket)
    except Exception:
        websocket_manager.manager.disconnect(websocket)


def _ensure_transformer_models() -> None:
    """Report Temporal Transformer model availability without creating untrained placeholders."""
    model_dir = settings.MODEL_DIR
    required_files = [
        "behavior_classifier.pt",
        "behavior_classifier_scaler.pkl",
    ]
    missing = [f for f in required_files if not os.path.exists(os.path.join(model_dir, f))]
    if missing:
        print(
            f"Missing Temporal Transformer model files in {model_dir}: {missing}. "
            "Temporal Transformer inference will return neutral scores until trained model weights are provided. "
            "Run `python -m app.transformer.train` or supply validated production weights before using Temporal Transformer risk signals."
        )

    try:
        pose_path = settings.POSE_MODEL_PATH
        if not os.path.exists(pose_path):
            print(
                f"Pose model not found at {pose_path}. "
                "CV processing will stay disabled until POSE_MODEL_PATH points to valid YOLOv8 pose weights."
            )
    except Exception:
        # Non-fatal; startup continues even if pose model check fails.
        pass

# Previously startup/shutdown handlers used @app.on_event which is deprecated
# in recent FastAPI versions; lifespan context manager above replaces them.

@app.get("/")
async def root():
    return {"message": "RailMind AI Backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
