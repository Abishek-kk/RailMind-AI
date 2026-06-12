"""Alert schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, model_validator

class AlertBase(BaseModel):
    person_id: str
    camera_id: str
    platform: str
    incident_type: str
    risk_score: float
    risk_level: str
    status: str = "active"
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
    escalation_status: Optional[str] = None
    escalation_error: Optional[str] = None
    notification_status: Optional[str] = None
    notification_error: Optional[str] = None
    is_false_positive: bool = False
    lstm_confidence: Optional[float] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    operator_assigned: Optional[str] = None
    resolved_at: Optional[datetime] = None


class AssignAlert(BaseModel):
    assignee: Optional[str] = None
    operator_assigned: Optional[str] = None

    @model_validator(mode="before")
    def normalize_assignee(cls, values):
        if isinstance(values, dict):
            if "assignee" not in values and "operator_assigned" in values:
                values["assignee"] = values["operator_assigned"]
        return values

    @model_validator(mode="after")
    def validate_assignee(self):
        if not self.assignee:
            raise ValueError("Missing assignee in payload")
        return self
