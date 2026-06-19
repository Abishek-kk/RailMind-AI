"""Tracked-person sequence database model."""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String, nullable=False, index=True)
    camera_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="SET NULL"), nullable=True)
    feature_sequence_json = Column(JSON, nullable=True)
    lstm_label = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    platform = relationship("Platform")
