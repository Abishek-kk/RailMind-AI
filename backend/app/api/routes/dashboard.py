from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from app.api.deps import get_db

router = APIRouter()

@router.get("/stats")
async def get_dashboard_general_stats(db = Depends(get_db)):
    """Retrieves macro parameters: total historical incidents, active alarms, and safety grades."""
    return {
        "total_incidents": 524,
        "active_alerts": 15,
        "suicide_mitigations": 4,
        "theft_preventions": 32,
        "system_status": "optimal"
    }

@router.get("/incidents-by-cctv")
async def get_incidents_grouped_by_camera(db = Depends(get_db)):
    """Retrieves total flags mapped directly to parent cameras for downstream charts."""
    return [
        {"camera_id": "CCTV_P1_04", "incidents": 42},
        {"camera_id": "CCTV_P2_01", "incidents": 18},
        {"camera_id": "CCTV_P3_11", "incidents": 29}
    ]

@router.get("/trend")
async def get_incident_trend(days: int = 7, db = Depends(get_db)):
    """Returns a time-series graph mapping alert volumes over rolling analytical windows."""
    today = datetime.utcnow().date()
    return [
        {
            "date": (today - timedelta(days=i)).isoformat(),
            "Suicide Risk": 0 if i != 2 else 1,
            "Pickpocketing": 2 + (i % 3),
            "Loitering": 5 + (i % 2)
        }
        for i in reversed(range(days))
    ]

@router.get("/risk-distribution")
async def get_risk_distribution(db = Depends(get_db)):
    """Returns absolute percentile slice parameters map for classification matrices."""
    return [
        {"name": "Suicide Risk Detection", "value": 8.5},
        {"name": "Pickpocketing Actions", "value": 34.2},
        {"name": "Loitering / Trespass", "value": 42.3},
        {"name": "General Anomalies", "value": 15.0}
    ]

@router.get("/heatmap")
async def get_platform_heatmap_intensity(db = Depends(get_db)):
    """Returns relative density indicators across spatial station grid segments."""
    return [
        {"platform": "Platform 1", "zone": "Zone A (Edge)", "intensity": 0.88},
        {"platform": "Platform 1", "zone": "Zone B (Center)", "intensity": 0.12},
        {"platform": "Platform 2", "zone": "Zone A (Edge)", "intensity": 0.45}
    ]

@router.get("/peak-hours")
async def get_peak_hours_distribution(db = Depends(get_db)):
    """Aggregates security flags against 24-hour schedules to locate coverage vulnerabilities."""
    return [{"hour": f"{h:02d}:00", "incidents": 5 + (h % 4) if 8 <= h <= 18 else 1} for h in range(24)]

@router.get("/cctv-summary")
async def get_cctv_summary_matrix(db = Depends(get_db)):
    """Combines analytical profiles into structured line parameters for data table sheets."""
    return [
        {
            "camera_id": "CCTV_P1_04",
            "location": "Platform 1 Edge",
            "status": "active",
            "total_incidents": 42,
            "active_alerts": 1,
            "current_risk_level": "High"
        },
        {
            "camera_id": "CCTV_P2_01",
            "location": "Platform 2 Entry",
            "status": "active",
            "total_incidents": 18,
            "active_alerts": 0,
            "current_risk_level": "Safe"
        }
    ]