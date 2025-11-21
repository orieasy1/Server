from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, Enum, ForeignKey
from sqlalchemy.sql import func
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
    SYSTEM_REMINDER = "SYSTEM_REMINDER"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
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

    related_pet_id = Column(Integer, ForeignKey("pets.pet_id"))
    related_user_id = Column(Integer, ForeignKey("users.user_id"))
    related_lat = Column(DECIMAL(10, 7))
    related_lng = Column(DECIMAL(10, 7))

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
