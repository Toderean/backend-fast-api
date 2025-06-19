# backend/models/call_session.py
from sqlalchemy import Column, String, DateTime, func
from backend.db import Base

class CallSession(Base):
    __tablename__ = "call_session"
    id         = Column(String, primary_key=True, index=True)
    session_key = Column(String, nullable=False)
    creator    = Column(String, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
