from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import get_async_db
from backend.models.message import Message
from backend.models.user import User
from backend.schemas.messages import MessageSendRequest
from backend.auth import get_current_user
from datetime import datetime
from sqlalchemy import select


router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/send")
async def send_message(
    request: MessageSendRequest,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(User).where(User.username == request.to)
    result = await db.execute(stmt)
    receiver = result.scalars().first()

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    new_msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=request.encrypted_content,
        timestamp=datetime.utcnow(),
        status="sent"
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    return {"message_id": new_msg.id, "status": new_msg.status}

@router.get("/with/{username}")
async def get_messages_with_user(
    username: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    other_user = result.scalars().first()

    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(Message).where(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        {
            "from": "me" if msg.sender_id == current_user.id else username,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "status": msg.status
        }
        for msg in messages
    ]

@router.get("/unread")
async def get_unread_count(
    for_user: str,
    db: Session = Depends(get_async_db)
):
    stmt = select(User).where(User.username == for_user)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(Message).where(
        (Message.receiver_id == user.id) & (Message.status == "sent")
    )
    result = await db.execute(stmt)
    count = len(result.scalars().all())

    return {"unread_count": count}

@router.post("/mark_seen")
async def mark_messages_seen(
    with_user: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(User).where(User.username == with_user)
    result = await db.execute(stmt)
    other = result.scalars().first()

    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(Message).where(
        (Message.sender_id == other.id) &
        (Message.receiver_id == current_user.id) &
        (Message.status == "sent")
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    for msg in messages:
        msg.status = "seen"

    await db.commit()
    return {"marked": len(messages)}
