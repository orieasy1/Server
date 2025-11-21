from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class NotificationRead(Base):
    __tablename__ = "notification_reads"

    id = Column(Integer, primary_key=True, autoincrement=True)

    notification_id = Column(
        Integer,
        ForeignKey("notifications.notification_id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    read_at = Column(DateTime, default=func.now(), nullable=False)

    # → "한 알림을 한 사람이 여러 번 읽어도 1회만 기록" 을 강제
    __table_args__ = (
        UniqueConstraint("notification_id", "user_id", name="uq_notification_read_user"),
    )

    # 관계 설정
    notification = relationship("Notification", backref="read_logs")
    user = relationship("User")
