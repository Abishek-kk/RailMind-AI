from fastapi import APIRouter, Depends
from app.api.deps import get_db
from app.api.routes.dashboard import get_incident_trend

router = APIRouter()

@router.get("/summary")
async def analytics_summary(days: int = 7, db = Depends(get_db)):
    return await get_incident_trend(days, db)

@router.get("/trend")
async def analytics_trend(days: int = 7, db = Depends(get_db)):
    return await get_incident_trend(days, db)

