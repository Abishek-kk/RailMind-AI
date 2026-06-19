from fastapi import APIRouter, Depends
from datetime import datetime, time, timedelta
from sqlalchemy import func, cast, Date, case
from app.api.deps import get_db
from app.analytics.heatmap import get_live_platform_heatmap, get_persistent_platform_heatmap
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.feed import Feed

router = APIRouter()

TREND_COLUMNS = ("Suicide Risk", "Pickpocketing", "Loitering")


def get_trend_bucket(incident_type: str) -> str | None:
    """Map stored incident labels onto dashboard chart series."""
    normalized = incident_type.lower()
    if "suicide" in normalized:
        return "Suicide Risk"
    if "pickpocket" in normalized or "theft" in normalized:
        return "Pickpocketing"
    if "loiter" in normalized or "trespass" in normalized:
        return "Loitering"
    return None


def build_incident_trend(alerts, days: int, today=None):
    today = today or datetime.utcnow().date()
    days = max(days, 1)
    rows = {
        today - timedelta(days=i): {
            "date": (today - timedelta(days=i)).isoformat(),
            **{column: 0 for column in TREND_COLUMNS},
        }
        for i in range(days)
    }

    for alert in alerts:
        alert_date = alert.timestamp.date()
        if alert_date not in rows:
            continue

        bucket = get_trend_bucket(alert.incident_type)
        if bucket:
            rows[alert_date][bucket] += 1

    return [rows[day] for day in sorted(rows)]

@router.get("/stats")
async def get_dashboard_general_stats(db = Depends(get_db)):
    """Retrieves macro parameters: total historical incidents, active alarms, and safety grades."""
    # Count total incidents from database
    total_incidents = db.query(func.count(Incident.id)).scalar() or 0
    
    # Count active alerts (status != 'resolved' or 'closed')
    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.status.in_(["active", "acknowledged"])
    ).scalar() or 0
    
    # Count high-risk alerts
    security_threats = db.query(func.count(Alert.id)).filter(
        Alert.risk_level.in_(["High", "Critical"])
    ).scalar() or 0
    
    # Count suicide-related alerts
    suicide_mitigations = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%suicide%")
    ).scalar() or 0
    
    # Count theft/pickpocketing-related alerts
    theft_preventions = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%theft%") | Alert.incident_type.ilike("%pickpocket%")
    ).scalar() or 0
    
    # Determine system status based on active alerts
    if active_alerts == 0:
        system_status = "optimal"
    elif security_threats == 0:
        system_status = "operational"
    else:
        system_status = "alert"
    
    return {
        "total_incidents": total_incidents,
        "active_alerts": active_alerts,
        "security_threats": security_threats,
        "suicide_mitigations": suicide_mitigations,
        "theft_preventions": theft_preventions,
        "system_status": system_status
    }

@router.get("/incidents-by-cctv")
async def get_incidents_grouped_by_camera(db = Depends(get_db)):
    """Retrieves total flags mapped directly to parent cameras for downstream charts."""
    # Group incidents by camera_id and count
    results = db.query(
        Alert.camera_id,
        func.count(Alert.id).label("incidents")
    ).group_by(Alert.camera_id).all()
    
    return [
        {"camera_id": camera_id, "incidents": count}
        for camera_id, count in results
    ]

@router.get("/trend")
async def get_incident_trend(days: int = 7, db = Depends(get_db)):
    """Returns a time-series graph mapping alert volumes over rolling analytical windows."""
    today = datetime.utcnow().date()
    days = max(days, 1)
    start_date = today - timedelta(days=days - 1)
    start_at = datetime.combine(start_date, time.min)

    # Fetch raw alerts and process in Python to avoid SQLAlchemy casting issues
    alerts = db.query(
        Alert.timestamp,
        Alert.incident_type,
    ).filter(
        Alert.timestamp >= start_at,
    ).all()

    rows = {
        today - timedelta(days=i): {
            "date": (today - timedelta(days=i)).isoformat(),
            **{column: 0 for column in TREND_COLUMNS},
        }
        for i in range(days)
    }

    # Process alerts in Python
    for alert in alerts:
        alert_date = alert.timestamp.date() if alert.timestamp else None
        if not alert_date or alert_date not in rows:
            continue

        bucket = get_trend_bucket(alert.incident_type)
        if bucket:
            rows[alert_date][bucket] += 1

    return [rows[day] for day in sorted(rows)]

@router.get("/risk-distribution")
async def get_risk_distribution(db = Depends(get_db)):
    """Returns absolute percentile slice parameters map for classification matrices."""
    total_alerts = db.query(func.count(Alert.id)).scalar() or 1
    
    # Count by incident type
    suicide_count = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%suicide%")
    ).scalar() or 0
    
    pickpocket_count = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%pickpocket%") | Alert.incident_type.ilike("%theft%")
    ).scalar() or 0
    
    loitering_count = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%loiter%") | Alert.incident_type.ilike("%trespass%")
    ).scalar() or 0
    
    anomaly_count = total_alerts - suicide_count - pickpocket_count - loitering_count
    
    # Calculate percentages
    suicide_pct = round((suicide_count / total_alerts) * 100, 1) if total_alerts > 0 else 0
    pickpocket_pct = round((pickpocket_count / total_alerts) * 100, 1) if total_alerts > 0 else 0
    loitering_pct = round((loitering_count / total_alerts) * 100, 1) if total_alerts > 0 else 0
    anomaly_pct = round((anomaly_count / total_alerts) * 100, 1) if total_alerts > 0 else 0
    
    return [
        {"name": "Suicide Risk Detection", "value": suicide_pct},
        {"name": "Pickpocketing Actions", "value": pickpocket_pct},
        {"name": "Loitering / Trespass", "value": loitering_pct},
        {"name": "General Anomalies", "value": anomaly_pct}
    ]

@router.get("/heatmap")
async def get_platform_heatmap_intensity(db = Depends(get_db)):
    """Returns relative density indicators across spatial station grid segments."""
    persistent_rows = get_persistent_platform_heatmap(db)
    if persistent_rows:
        return persistent_rows

    live_rows = get_live_platform_heatmap()
    if live_rows:
        return live_rows

    from app.analytics.heatmap import HeatmapGenerator
    
    # Get all recent alerts with bounding box data (last 1000 for performance)
    alerts = db.query(Alert).filter(
        Alert.bounding_box.isnot(None)
    ).order_by(Alert.timestamp.desc()).limit(1000).all()
    
    if not alerts:
        return []  # No data available
    
    # Group alerts by camera to generate per-camera heatmaps
    camera_heatmaps = {}
    for alert in alerts:
        camera_id = alert.camera_id
        if camera_id not in camera_heatmaps:
            # Assume standard video frame dimensions (adjust if different)
            camera_heatmaps[camera_id] = {
                "generator": HeatmapGenerator(1920, 1080, grid_size=32),
                "platform": alert.platform
            }
        
        # Convert bounding box to pose format for the heatmap generator
        if alert.bounding_box and isinstance(alert.bounding_box, dict):
            bbox = alert.bounding_box
            # Assume bounding_box has keys like 'x1', 'y1', 'x2', 'y2' or 'left', 'top', 'right', 'bottom'
            if 'x1' in bbox and 'y1' in bbox and 'x2' in bbox and 'y2' in bbox:
                center_x = (bbox['x1'] + bbox['x2']) / 2
                center_y = (bbox['y1'] + bbox['y2']) / 2
            elif 'left' in bbox and 'top' in bbox and 'right' in bbox and 'bottom' in bbox:
                center_x = (bbox['left'] + bbox['right']) / 2
                center_y = (bbox['top'] + bbox['bottom']) / 2
            else:
                continue
            
            pose = {"center": (center_x, center_y)}
            camera_heatmaps[camera_id]["generator"].update([pose])
    
    # Collect hotspots from all cameras
    rows = []
    for camera_id, data in camera_heatmaps.items():
        generator = data["generator"]
        for hotspot in generator.identify_hotspots():
            max_value = float(generator.heatmap.max()) if generator.heatmap.size else 1.0
            intensity = min(1.0, hotspot["value"] / max(max_value, 1.0))
            rows.append({
                "platform": data["platform"],
                "zone": f"{camera_id} R{hotspot['row']:02d} C{hotspot['col']:02d}",
                "intensity": round(intensity, 4)
            })
    
    # Sort by intensity (highest first)
    return sorted(rows, key=lambda x: x["intensity"], reverse=True)

@router.get("/peak-hours")
async def get_peak_hours_distribution(db = Depends(get_db)):
    """Aggregates security flags against 24-hour schedules to locate coverage vulnerabilities."""
    # Count alerts by hour of day
    hourly_counts = {}
    for h in range(24):
        hourly_counts[h] = 0
    
    alerts = db.query(Alert).all()
    for alert in alerts:
        hour = alert.timestamp.hour
        hourly_counts[hour] += 1
    
    return [
        {"hour": f"{h:02d}:00", "incidents": hourly_counts[h]}
        for h in range(24)
    ]

@router.get("/cctv-summary")
async def get_cctv_summary_matrix(db = Depends(get_db)):
    """Combines analytical profiles into structured line parameters for data table sheets."""
    feeds = db.query(Feed).all()
    
    result = []
    for feed in feeds:
        # Count total incidents for this camera
        total_incidents = db.query(func.count(Alert.id)).filter(
            Alert.camera_id == feed.id
        ).scalar() or 0
        
        # Count active alerts for this camera
        active_alerts = db.query(func.count(Alert.id)).filter(
            Alert.camera_id == feed.id,
            Alert.status.in_(["active", "acknowledged"])
        ).scalar() or 0
        
        # Get max risk level for this camera
        max_risk = db.query(Alert.risk_level).filter(
            Alert.camera_id == feed.id
        ).order_by(
            # Order by risk level priority
            case(
                (Alert.risk_level == "Critical", 1),
                (Alert.risk_level == "High", 2),
                (Alert.risk_level == "Medium", 3),
                (Alert.risk_level == "Low", 4),
                else_=5
            )
        ).first()
        
        current_risk_level = max_risk[0] if max_risk else "Safe"

        last_alert = db.query(Alert.timestamp).filter(
            Alert.camera_id == feed.id
        ).order_by(Alert.timestamp.desc()).first()
        last_incident = last_alert[0].strftime("%Y-%m-%d %H:%M") if last_alert and last_alert[0] else None
        
        result.append({
            "camera_id": feed.id,
            "location": feed.name,
            "status": feed.status,
            "total_incidents": total_incidents,
            "active_alerts": active_alerts,
            "current_risk_level": current_risk_level,
            "last_incident": last_incident,
        })
    
    return result
