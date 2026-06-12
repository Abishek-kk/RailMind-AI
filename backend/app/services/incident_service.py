"""Incident service business logic."""
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.incident import Incident


class IncidentService:
    """Handles incident operations."""

    def __init__(self, db: Session):
        self.db = db

    def list_incidents(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Incident]:
        query = self.db.query(Incident)

        if filters:
            if filters.get("camera_id"):
                query = query.filter(Incident.camera_id == filters["camera_id"])
            if filters.get("incident_type"):
                query = query.filter(Incident.incident_type == filters["incident_type"])
            if filters.get("risk_level"):
                query = query.filter(Incident.risk_level == filters["risk_level"])
            if filters.get("status"):
                query = query.filter(Incident.status == filters["status"])
            if filters.get("date_from"):
                query = query.filter(Incident.timestamp >= filters["date_from"])
            if filters.get("date_to"):
                query = query.filter(Incident.timestamp <= filters["date_to"])

        query = query.order_by(Incident.timestamp.desc())
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_incident(self, incident_id: int) -> Optional[Incident]:
        return self.db.query(Incident).filter(Incident.id == incident_id).first()
    def is_track_acknowledged(self, person_id: str, camera_id: str) -> bool:
        """Return True when a track has an acknowledged/resolved incident for the same camera."""
        return (
            self.db.query(Incident)
            .join(Alert, Incident.alert_id == Alert.id)
            .filter(Alert.person_id == person_id)
            .filter(Alert.camera_id == camera_id)
            .filter(Incident.status.in_(["acknowledged", "resolved", "false_positive"]))
            .count()
            > 0
        )
    def create_incident(self, payload: Dict[str, Any]) -> Incident:
        incident = Incident(**payload)
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def acknowledge_incident(self, incident_id: int) -> Optional[Incident]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = "acknowledged"
        incident.acknowledged_at = func.now()
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def resolve_incident(self, incident_id: int, resolution_notes: Optional[str] = None) -> Optional[Incident]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = "resolved"
        incident.resolved_at = func.now()
        if resolution_notes is not None:
            incident.resolution_notes = resolution_notes
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def mark_false_positive(
        self,
        incident_id: int,
        staff_id: str,
        notes: Optional[str] = None,
    ) -> Optional[Incident]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = "false_positive"
        incident.false_positive = True
        incident.false_positive_reported_by = staff_id
        incident.false_positive_notes = notes
        self.db.commit()
        self.db.refresh(incident)
        return incident
