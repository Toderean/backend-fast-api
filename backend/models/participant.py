from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from backend.db import Base

class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, ForeignKey("call_session.id"))
    user_id = Column(String, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
