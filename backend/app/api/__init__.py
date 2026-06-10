from fastapi import APIRouter
from app.api.routes import alerts, dashboard, feeds, health

api_router = APIRouter()

# Include sub-routers with clean prefixes and tagging for OpenAPI docs
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])