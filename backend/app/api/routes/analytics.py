from fastapi import APIRouter, Depends
from app.api.deps import get_db
from app.api.routes.dashboard import get_incident_trend, get_platform_heatmap_intensity

router = APIRouter()

@router.get("/summary")
async def analytics_summary(days: int = 7, db = Depends(get_db)):
    return await get_incident_trend(days, db)

@router.get("/heatmap")
async def analytics_heatmap(db = Depends(get_db)):
    return await get_platform_heatmap_intensity(db)
