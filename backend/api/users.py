from http.client import HTTPException

from fastapi import APIRouter, Depends, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_async_db
from backend.auth import get_current_user
from backend.models.user import User
from backend.schemas.user import UserRead, StatusUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}

@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/{username}", response_model=UserRead)
async def get_user(username: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, detail="User not found")
    return user

@router.post("/status")
async def update_status(
    payload: StatusUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    current_user.status = payload.status
    await db.commit()
    return {"status": "updated"}


@router.get("/status/{username}")
async def get_status(username: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": username, "status": user.status}


