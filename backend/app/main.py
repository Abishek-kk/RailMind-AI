"""Main FastAPI application entry point for the RailMind AI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core import websocket_manager
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Ensure the common frontend origins are allowed for CORS (helps HTTP requests).
frontend_origins = ["http://localhost:5173", "http://localhost:8080"]
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
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
    origin = websocket.headers.get("origin")
    allowed = set(settings.BACKEND_CORS_ORIGINS or [])
    try:
        if origin and origin not in allowed:
            # Reject the handshake by closing with policy violation
            await websocket.close(code=1008)
            return

        await websocket_manager.manager.connect(websocket)
        try:
            while True:
                # Keep the connection open to allow server pushes; echo incoming pings if any
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.manager.disconnect(websocket)
    except Exception:
        # Ensure clean disconnect on unexpected errors
        try:
            websocket_manager.manager.disconnect(websocket)
        except Exception:
            pass

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
