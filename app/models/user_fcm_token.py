from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.models.base import Base


class UserFcmToken(Base):
    """
    Per-device FCM token store to support multiple logins per user.
    """

    __tablename__ = "user_fcm_tokens"

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    fcm_token = Column(String(255), nullable=False, unique=True)
    device_id = Column(String(128), nullable=True)
    platform = Column(String(32), nullable=True, default="android")
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_user_device"),
    )
