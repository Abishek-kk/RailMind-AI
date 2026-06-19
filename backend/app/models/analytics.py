"""Aggregated analytics database model."""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="SET NULL"), nullable=True)
    camera_id = Column(String, nullable=True, index=True)
    zone = Column(String, nullable=True, index=True)
    incident_count = Column(Integer, nullable=False, default=0)
    avg_risk_score = Column(Float, nullable=False, default=0.0)
    false_positive_count = Column(Integer, nullable=False, default=0)
    hotspot_count = Column(Integer, nullable=False, default=0)
    hotspot_intensity = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    platform = relationship("Platform")
