from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    public_key: Optional[str] = None

class UserCreate(UserBase):
    password: str

class StatusUpdateRequest(BaseModel):
    status: str

class UserRead(UserBase):
    id: int
    email_confirmed: bool
    public_key: Optional[str] = None
    status: str

    class Config:
        orm_mode = True

