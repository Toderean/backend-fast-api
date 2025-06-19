from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class CallSessionRead(BaseModel):
    id: str
    created_at: datetime
    session_key: Optional[str]
    class Config:
        orm_mode = True

class ParticipantRead(BaseModel):
    user_id: str
    joined_at: datetime
    class Config:
        orm_mode = True
