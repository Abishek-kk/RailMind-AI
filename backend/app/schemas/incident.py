"""Incident schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IncidentBase(BaseModel):
    alert_id: Optional[int] = None
    camera_id: str
    incident_type: str
    risk_score: float
    risk_level: str
    status: str = "unacknowledged"


class IncidentCreate(IncidentBase):
    """Schema for creating incident records."""


class IncidentRead(IncidentBase):
    id: int
    timestamp: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    false_positive: bool = False
    false_positive_reported_by: Optional[str] = None
    false_positive_notes: Optional[str] = None

    class Config:
        orm_mode = True


class IncidentResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None


class IncidentFalsePositiveRequest(BaseModel):
    staff_id: str
    notes: Optional[str] = None
