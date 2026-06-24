"""Alert database model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(String, nullable=False)
    camera_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String, nullable=False, default="Safe")
    status = Column(String, nullable=False, default="active")
    escalation_level = Column(Integer, nullable=False, default=0)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String, nullable=True)
    is_false_positive = Column(Boolean, nullable=False, default=False)
    lstm_confidence = Column(Float, nullable=True)
    escalation_triggered_at = Column(DateTime(timezone=True), nullable=True)
    escalation_status = Column(String, nullable=True)
    escalation_error = Column(String, nullable=True)
    notification_status = Column(String, nullable=True)
    notification_error = Column(String, nullable=True)
    bounding_box = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    operator_assigned = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    video_snippet_url = Column(String, nullable=True)
    reasoning_mode = Column(String, nullable=True)
