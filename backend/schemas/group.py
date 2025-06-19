from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class GroupCreate(BaseModel):
    name: str


class GroupRead(BaseModel):
    id: int
    name: str
    creator_id: int
    creator_username: str

    class Config:
        orm_mode = True