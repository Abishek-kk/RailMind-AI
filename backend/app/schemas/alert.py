"""Alert schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

class AlertBase(BaseModel):
    person_id: str
    camera_id: str
    platform: str
    incident_type: str
    risk_score: float
    risk_level: str
    status: str = "unacknowledged"
    bounding_box: Optional[List[int]] = None
    operator_assigned: Optional[str] = None
    video_snippet_url: Optional[str] = None

class AlertCreate(AlertBase):
    """Schema for creating alert records."""

class AlertRead(AlertBase):
    id: int
    timestamp: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    escalation_level: int = 0
    escalation_triggered_at: Optional[datetime] = None
    is_false_positive: bool = False
    lstm_confidence: Optional[float] = None
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    operator_assigned: Optional[str] = None
    resolved_at: Optional[datetime] = None
