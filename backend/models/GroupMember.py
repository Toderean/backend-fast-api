from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db import Base

class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String, nullable=False)  # 'joined', 'invited', 'pending'
    joined_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="members")
    user = relationship("User", backref="group_memberships")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="unique_member_per_group"),
        CheckConstraint("status IN ('joined', 'invited', 'pending')", name="valid_member_status"),
    )