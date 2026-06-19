from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from app.api.deps import get_db
from app.api.routes.dashboard import get_incident_trend
from app.analytics.heatmap import get_persistent_platform_heatmap
from app.models.incident import Incident
from app.models.alert import Alert

router = APIRouter()


@router.get("/summary")
async def analytics_summary(days: int = 7, db = Depends(get_db)):
    return await get_incident_trend(days, db)


@router.get("/trend")
async def analytics_trend(days: int = 7, db = Depends(get_db)):
    return await get_incident_trend(days, db)


@router.get("/heatmap")
async def analytics_heatmap(
    platform: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return aggregated incident heatmap points grouped by platform and camera.

    Each returned object contains: platform, camera_id, x, y, incident_count,
    avg_risk_score. `x` and `y` are the average centers of associated alert
    bounding boxes when available, otherwise null.
    """
    persisted_hotspots = get_persistent_platform_heatmap(db, platform=platform)
    if persisted_hotspots and not camera_id and not date_from and not date_to:
        return persisted_hotspots

    # Build base query for incidents joined with alerts (alert may be null)
    q = db.query(Incident, Alert).outerjoin(Alert, Incident.alert_id == Alert.id)

    if platform:
        q = q.filter(Incident.platform == platform)
    if camera_id:
        q = q.filter(Incident.camera_id == camera_id)
    if date_from:
        q = q.filter(Incident.timestamp >= date_from)
    if date_to:
        q = q.filter(Incident.timestamp <= date_to)

    rows = q.all()

    # Aggregate in Python per (platform, camera_id)
    groups: Dict[tuple, Dict[str, Any]] = {}
    for incident, alert in rows:
        key = (incident.platform, incident.camera_id)
        entry = groups.setdefault(key, {
            "platform": incident.platform,
            "camera_id": incident.camera_id,
            "incident_count": 0,
            "risk_total": 0.0,
            "x_total": 0.0,
            "y_total": 0.0,
            "bbox_count": 0,
        })

        entry["incident_count"] += 1
        entry["risk_total"] += float(incident.risk_score or 0.0)

        # If there's an associated alert with a bounding_box, try to compute center
        if alert and getattr(alert, "bounding_box", None):
            bbox = alert.bounding_box
            cx = cy = None
            if isinstance(bbox, dict):
                if all(k in bbox for k in ("x1", "y1", "x2", "y2")):
                    cx = (bbox["x1"] + bbox["x2"]) / 2
                    cy = (bbox["y1"] + bbox["y2"]) / 2
                elif all(k in bbox for k in ("left", "top", "right", "bottom")):
                    cx = (bbox["left"] + bbox["right"]) / 2
                    cy = (bbox["top"] + bbox["bottom"]) / 2
            elif isinstance(bbox, list) and len(bbox) >= 4:
                # Assume [x1, y1, x2, y2]
                try:
                    cx = (float(bbox[0]) + float(bbox[2])) / 2
                    cy = (float(bbox[1]) + float(bbox[3])) / 2
                except Exception:
                    cx = cy = None

            if cx is not None and cy is not None:
                entry["x_total"] += cx
                entry["y_total"] += cy
                entry["bbox_count"] += 1

    # Prepare output
    out: List[Dict[str, Any]] = []
    for (plat, cam), v in groups.items():
        count = v["incident_count"]
        avg_risk = round(v["risk_total"] / count, 4) if count > 0 else 0.0
        if v["bbox_count"] > 0:
            x = round(v["x_total"] / v["bbox_count"], 2)
            y = round(v["y_total"] / v["bbox_count"], 2)
        else:
            x = None
            y = None

        out.append({
            "platform": plat,
            "camera_id": cam,
            "x": x,
            "y": y,
            "incident_count": count,
            "avg_risk_score": avg_risk,
        })

    return out


@router.get("/lstm-performance")
async def analytics_lstm_performance(db = Depends(get_db)):
    """Return simple LSTM performance metrics derived from alerts/incidents."""

    # Total predictions: alerts that have an LSTM confidence value
    total_predictions = db.query(func.count(Alert.id)).filter(Alert.lstm_confidence.isnot(None)).scalar() or 0

    avg_confidence = db.query(func.avg(Alert.lstm_confidence)).filter(Alert.lstm_confidence.isnot(None)).scalar() or 0.0
    try:
        avg_confidence = float(avg_confidence)
    except Exception:
        avg_confidence = 0.0

    # False positives: alerts marked is_false_positive plus incidents flagged false_positive
    alert_false = db.query(func.count(Alert.id)).filter(Alert.is_false_positive == True).scalar() or 0
    incident_false = db.query(func.count(Incident.id)).filter(Incident.false_positive == True).scalar() or 0
    false_positive_count = alert_false + incident_false

    false_positive_rate = (false_positive_count / total_predictions) if total_predictions > 0 else 0.0

    # Per-class counts from alerts (best-effort mapping)
    per_class = {
        "Normal": 0,
        "Suicide Risk": 0,
        "Pickpocketing": 0,
        "Security Threat": 0,
    }

    # Count alerts by simple keyword matching
    per_class["Suicide Risk"] = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%suicide%")
    ).scalar() or 0

    per_class["Pickpocketing"] = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%pickpocket%") | Alert.incident_type.ilike("%theft%")
    ).scalar() or 0

    per_class["Security Threat"] = db.query(func.count(Alert.id)).filter(
        Alert.incident_type.ilike("%security%") | Alert.incident_type.ilike("%threat%")
    ).scalar() or 0

    # Normal == alerts not matching the above categories
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    matched = per_class["Suicide Risk"] + per_class["Pickpocketing"] + per_class["Security Threat"]
    per_class["Normal"] = max(0, (total_alerts - matched))

    return {
        "total_predictions": int(total_predictions),
        "avg_confidence": float(round(avg_confidence, 4)),
        "false_positive_rate": float(round(false_positive_rate, 4)),
        "false_positive_count": int(false_positive_count),
        "per_class_counts": per_class,
    }

