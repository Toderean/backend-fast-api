from typing import Optional
from pydantic import BaseModel

class SignalingCreate(BaseModel):
    call_id: str
    type: str
    content: str
    target_user: Optional[str] = None

class SignalingRead(SignalingCreate):
    id: int
    sender: str

    class Config:
        orm_mode = True
