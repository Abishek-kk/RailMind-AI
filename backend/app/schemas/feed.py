"""Feed schemas"""
from datetime import datetime

from pydantic import BaseModel

class FeedRead(BaseModel):
    id: str
    name: str
    status: str
    fps: float
    created_at: datetime

    class Config:
        orm_mode = True
