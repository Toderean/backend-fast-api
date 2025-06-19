from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GroupMemberRead(BaseModel):
    id: int
    group_id: int
    user_id: int
    status: str
    joined_at: Optional[datetime] = None
    group_name: str
    username: str

    class Config:
        orm_mode = True


class GroupMemberUpdate(BaseModel):
    user_id: int