"""Persistent false-positive rate alert for a station/platform."""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class StationFpAlert(Base):
    __tablename__ = "station_fp_alerts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False, unique=True, index=True)
    fp_rate = Column(Float, nullable=False)
    alerted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
