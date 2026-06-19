"""Operator feedback database model."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True, index=True)
    training_run_id = Column(Integer, ForeignKey("training_runs.id", ondelete="SET NULL"), nullable=True)
    is_false_positive = Column(Boolean, nullable=False, default=False)
    corrected_label = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    alert = relationship("Alert")
    staff = relationship("Staff")
    training_run = relationship("TrainingRun")
