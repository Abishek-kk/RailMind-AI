"""Alert service business logic"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.alert import Alert

class AlertService:
    """Handles alert operations"""

    def __init__(self, db: Session):
        self.db = db

    def list_alerts(self, filters: Optional[Dict[str, str]] = None) -> List[Alert]:
        query = self.db.query(Alert)
        if filters:
            if filters.get("risk_level"):
                query = query.filter(Alert.risk_level == filters["risk_level"])
            if filters.get("status"):
                query = query.filter(Alert.status == filters["status"])
            if filters.get("platform"):
                query = query.filter(Alert.platform == filters["platform"])
        return query.order_by(Alert.timestamp.desc()).all()

    def create_alert(self, payload: Dict[str, any]) -> Alert:
        alert = Alert(**payload)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_alert(self, alert_id: int) -> Optional[Alert]:
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def acknowledge_alert(self, alert_id: int, staff_id: Optional[str] = None) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        if staff_id is not None:
            alert.acknowledged_by = staff_id
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def escalate_alert(self, alert_id: int) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.escalation_level = (alert.escalation_level or 0) + 1
        alert.escalation_triggered_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        alert.status = "resolved"
        alert.resolved_at = func.now()
        self.db.commit()
        self.db.refresh(alert)
        return alert
