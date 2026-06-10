from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertRead

router = APIRouter()

@router.get("", response_model=List[AlertRead])
async def get_alerts(
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
    if risk_level:
        query = query.filter(Alert.risk_level == risk_level)
    if status:
        query = query.filter(Alert.status == status)
    if platform:
        query = query.filter(Alert.platform == platform)

    return query.order_by(Alert.timestamp.desc()).all()

@router.get("/stats")
async def get_alert_stats(db: Session = Depends(get_db)):
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    high_risk = db.query(func.count(Alert.id)).filter(Alert.risk_level == "High Risk").scalar() or 0
    medium_risk = db.query(func.count(Alert.id)).filter(Alert.risk_level == "Medium Risk").scalar() or 0
    low_risk = db.query(func.count(Alert.id)).filter(Alert.risk_level == "Low Risk").scalar() or 0
    resolved = db.query(func.count(Alert.id)).filter(Alert.status == "resolved").scalar() or 0

    return {
        "total_alerts": total_alerts,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "resolved": resolved,
    }

@router.get("/{id}", response_model=AlertRead)
async def get_alert(id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert record not found")
    return alert

@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    alert_obj = Alert(**alert.dict())
    db.add(alert_obj)
    db.commit()
    db.refresh(alert_obj)
    return alert_obj

@router.patch("/{id}/acknowledge", response_model=AlertRead)
async def acknowledge_alert(id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert record not found")
    alert.status = "acknowledged"
    alert.operator_assigned = "Staff_Member_09"
    db.commit()
    db.refresh(alert)
    return alert

@router.patch("/{id}/resolve", response_model=AlertRead)
async def resolve_alert(id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert record not found")
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
