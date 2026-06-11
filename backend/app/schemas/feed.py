"""Feed schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class FeedCreate(BaseModel):
    id: str
    name: str
    source_url: str
    fps: Optional[float] = 30.0


class FeedRead(BaseModel):
    id: str
    name: str
    status: str
    fps: float
    source_url: Optional[str] = None
    stream_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
