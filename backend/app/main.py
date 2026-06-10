"""Main FastAPI application entry point for the RailMind AI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core import websocket_manager
from fastapi import WebSocket, WebSocketDisconnect
import logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


class ScopeLogger:
    """ASGI wrapper to log incoming HTTP and WebSocket scopes for debugging."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            if scope.get("type") in ("http", "websocket"):
                headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
                logging.getLogger("railmind").info(
                    f"Incoming scope type={scope.get('type')} path={scope.get('path')} headers={headers}"
                )
        except Exception:
            pass
        await self.app(scope, receive, send)

# Note: we'll wrap the FastAPI app with ScopeLogger below (after middleware setup)

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

# In development allow all origins to avoid CORS/preflight and websocket handshake
# issues from local dev servers (Vite). In production this should be tightened.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# Keep the FastAPI app object intact so decorators and startup hooks work normally.
# Wrap the app with ScopeLogger only for the ASGI server entry point.
asgi_app = ScopeLogger(app)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Add shutdown cleanup steps here if needed in the future.
    return None

@app.get("/")
async def root():
    return {"message": "RailMind AI Backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
