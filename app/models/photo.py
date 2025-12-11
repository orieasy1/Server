from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class Photo(Base):
    __tablename__ = "photos"

    photo_id = Column(Integer, primary_key=True, autoincrement=True)
    walk_id = Column(Integer, ForeignKey("walks.walk_id"), nullable=False)
    image_url = Column(String(255), nullable=False)
    uploaded_by = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,  # 사용자 삭제 시 사진은 유지하고 업로더만 비움
    )
    caption = Column(String(255))

    created_at = Column(DateTime, default=func.now())
