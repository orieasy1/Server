from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base
import enum

class MemberRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"

class FamilyMember(Base):
    __tablename__ = "family_members"

    member_id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, ForeignKey("families.family_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    role = Column(Enum(MemberRole), default=MemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=func.now())
