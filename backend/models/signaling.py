from sqlalchemy import Column, Integer, String, Text
from backend.db import Base

class SignalingData(Base):
    __tablename__ = "signaling_data"
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, index=True)
    sender = Column(String, index=True)
    target_user = Column(String, index=True)
    type = Column(String)
    content = Column(Text, nullable=False)