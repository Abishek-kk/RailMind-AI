"""Incident database model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, nullable=True)
    camera_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String, nullable=False, default="Safe")
    status = Column(String, nullable=False, default="unacknowledged")
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(String, nullable=True)
    false_positive = Column(Boolean, nullable=False, default=False)
    false_positive_reported_by = Column(String, nullable=True)
    false_positive_notes = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
