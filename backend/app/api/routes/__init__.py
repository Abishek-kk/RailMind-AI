"""
API Routes Package Aggregator
Combines individual sub-routers (alerts, dashboard, feeds, health) into a unified API router.
"""

from fastapi import APIRouter
from .alerts import router as alerts_router
from .dashboard import router as dashboard_router
from .feeds import router as feeds_router
from .health import router as health_router
from .incidents import router as incidents_router

# Initialize the main aggregator router
api_router = APIRouter()

# Mount sub-routers with corresponding endpoint prefixes and Swagger UI tags
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(feeds_router, prefix="/feeds", tags=["Feeds"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])

__all__ = ["api_router"]
