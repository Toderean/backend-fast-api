import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.db import get_async_db
from backend.models.call_session import CallSession
from backend.models.participant import Participant
from backend.schemas.call import CallSessionRead
from backend.schemas.call import ParticipantRead
from backend.auth import get_current_user
from backend.models.user import User


class CallJoinRequest(BaseModel):
    session_key: Optional[str] = None

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("/invitations")
async def get_invitations(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    stmt = select(Participant).where(Participant.user_id == user.username)
    res = await db.execute(stmt)
    calls = res.scalars().all()
    call_ids = [p.call_id for p in calls]
    if not call_ids:
        return []
    session_q = await db.execute(
        select(CallSession).where(CallSession.id.in_(call_ids))
    )
    sessions = session_q.scalars().all()
    return [
        {"call_id": s.id, "creator": s.creator}
        for s in sessions
    ]


@router.post("/{call_id}/accept")
async def accept_call(
    call_id: str,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    await db.execute(
        delete(Participant).where(Participant.call_id == call_id, Participant.user_id == user.username)
    )
    await db.commit()
    return {"detail": f"{user.username} accepted {call_id}"}



@router.post("/{call_id}/join")
async def join_call(
    call_id: str,
    req : CallJoinRequest,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),

):
    session_key = req.session_key
    session = await db.get(CallSession, call_id)
    if not session:
        if not session_key:
            raise HTTPException(400, detail="session_key required to create session")
        session = CallSession(id=call_id, creator=user.username, session_key=session_key)
        db.add(session)
        await db.commit()
    part = Participant(call_id=call_id, user_id=user.username)
    db.add(part)
    await db.commit()
    return {"detail": f"{user.username} joined {call_id}"}


@router.post("/{call_id}/leave")
async def leave_call(
    call_id: str,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    await db.execute(
      delete(Participant)
      .where(Participant.call_id == call_id, Participant.user_id == user.username)
    )
    await db.commit()
    return {"detail": f"{user.username} left {call_id}"}


@router.get(
    "/{call_id}/participants",
    response_model=list[ParticipantRead],
)
async def list_participants(
    call_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    q = await db.execute(
        select(Participant).where(Participant.call_id == call_id)
    )
    return q.scalars().all()


@router.get(
    "/{call_id}",
    response_model=CallSessionRead,
)
async def get_call_session(
    call_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    q = await db.execute(select(CallSession).where(CallSession.id == call_id))
    session = q.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Call not found")
    return session

@router.post("/group")
async def create_group_call(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    participants = payload.get("participants", [])
    session_key = payload.get("session_key")
    if not participants:
        raise HTTPException(400, detail="Selectează cel puțin un participant")
    call_id = f"group_{uuid.uuid4().hex[:8]}"
    session = CallSession(id=call_id, creator=user.username, session_key=session_key)
    db.add(session)
    db.add(Participant(call_id=call_id, user_id=user.username))
    for username in set(participants):
        if username != user.username:
            db.add(Participant(call_id=call_id, user_id=username))
    await db.commit()
    return {
        "call_id": call_id,
        "creator": user.username,
        "participants": list(set(participants + [user.username]))
    }

@router.get("/{call_id}/session_key")
async def get_session_key(
    call_id: str,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    session = await db.get(CallSession, call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Call not found")

    q = await db.execute(
        select(Participant).where(
            Participant.call_id == call_id,
            Participant.user_id == user.username
        )
    )
    participant = q.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=403, detail="Nu ai acces la această sesiune")

    return {"session_key": session.session_key}


