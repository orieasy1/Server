from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class NotificationType(enum.Enum):
    REQUEST = "REQUEST"
    INVITE_ACCEPTED = "INVITE_ACCEPTED"
    INVITE_REJECTED = "INVITE_REJECTED"
    ACTIVITY_START = "ACTIVITY_START"
    FAMILY_ROLE_CHANGED = "FAMILY_ROLE_CHANGED"
    ACTIVITY_END = "ACTIVITY_END"
    PET_UPDATE = "PET_UPDATE"
    SYSTEM_RANKING = "SYSTEM_RANKING"
    SYSTEM_WEATHER = "SYSTEM_WEATHER"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
    PET_MEMBER_LEFT = "PET_MEMBER_LEFT"
    SOS = "SOS"
    SOS_RESOLVED = "SOS_RESOLVED"


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)

    family_id = Column(Integer, ForeignKey("families.family_id"))
    target_user_id = Column(Integer, ForeignKey("users.user_id"))

    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(String(255), nullable=False)

    # 새로운 필드 ⭐
    related_pet_id = Column(Integer, ForeignKey("pets.pet_id"))
    related_user_id = Column(Integer, ForeignKey("users.user_id"))

    # 공유 요청 승인/거절을 위한 request_id ⭐
    related_request_id = Column(Integer, ForeignKey("pet_share_requests.request_id"), nullable=True)

    related_lat = Column(DECIMAL(10, 7))
    related_lng = Column(DECIMAL(10, 7))

    created_at = Column(DateTime, default=func.now())

    # relationships
    related_pet = relationship("Pet", foreign_keys=[related_pet_id])
    related_user = relationship("User", foreign_keys=[related_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    related_request = relationship("PetShareRequest", foreign_keys=[related_request_id])
