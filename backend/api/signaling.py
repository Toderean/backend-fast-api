# backend/api/signaling.py
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from backend.db import get_async_db
from backend.models.signaling import SignalingData
from backend.schemas.signaling import SignalingCreate, SignalingRead
from backend.auth import get_current_user
from backend.models.user import User
from backend.models.call_session import CallSession
from backend.models.participant import Participant

router = APIRouter(prefix="/signaling", tags=["Signaling"])

@router.post("/send", response_model=SignalingRead)
async def send_signaling(
    data: SignalingCreate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    record = SignalingData(
        call_id=data.call_id,
        sender=user.username,
        type=data.type,
        content=data.content,
        target_user=data.target_user
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{call_id}/{type}", response_model=List[SignalingRead])
async def get_signaling(
    call_id: str,
    type: str,
    for_user: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):

    result = await db.execute(
        select(SignalingData).where(
            SignalingData.call_id == call_id,
            SignalingData.type == type,
            (SignalingData.target_user == for_user)
        )
    )
    return result.scalars().all()



@router.get("/{username}", response_model=List[SignalingRead])
async def get_offers_for_user(
    username: str,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    stmt = select(SignalingData).where(
        and_(
            SignalingData.call_id.like(f"%_{username}"),
            SignalingData.type == "offer"
        )
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signaling(
    call_id: str,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    await db.execute(delete(SignalingData).where(SignalingData.call_id == call_id))
    await db.execute(delete(Participant).where(Participant.call_id == call_id))
    await db.execute(delete(CallSession).where(CallSession.id == call_id))
    await db.commit()


