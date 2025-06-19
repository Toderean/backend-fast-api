from sqlalchemy import Column, Integer, String, Boolean
from backend.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    public_key = Column(String, nullable=True)
    email_confirmed = Column(Boolean, default=False)
    confirmation_token = Column(String, nullable=True)
    status = Column(String(20), default="available")
