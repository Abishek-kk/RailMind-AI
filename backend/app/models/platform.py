"""Platform configuration database model."""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, nullable=False, index=True)
    platform_number = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    camera_ids_json = Column(JSON, nullable=False, default=list)
    edge_zone_config_json = Column(JSON, nullable=True)
    risk_config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
