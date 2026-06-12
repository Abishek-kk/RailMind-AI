"""Pydantic schemas for Staff"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StaffBase(BaseModel):
    name: str
    platform_zone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class StaffCreate(StaffBase):
    pass


class StaffRead(StaffBase):
    id: int
    is_available: bool
    last_acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StaffAvailabilityUpdate(BaseModel):
    is_available: bool
