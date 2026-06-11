"""Feed database model"""
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func

from app.core.database import Base

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="inactive")
    fps = Column(Float, nullable=False, default=0.0)
    source_url = Column(String, nullable=True)
    stream_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
