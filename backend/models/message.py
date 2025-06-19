# app/models/message.py
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from datetime import datetime
from backend.db import Base

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(String, ForeignKey("call_session.id"), nullable=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="sent")
