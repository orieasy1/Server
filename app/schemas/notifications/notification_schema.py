# app/schemas/notifications/notification_schema.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.error_schema import ErrorResponse


# -------------------------
# Related Sub Schemas
# -------------------------
class RelatedPetSchema(BaseModel):
    pet_id: int
    name: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class RelatedUserSchema(BaseModel):
    user_id: int
    nickname: str
    profile_img_url: Optional[str] = None

    class Config:
        from_attributes = True


# -------------------------
# Single Notification Item
# -------------------------
class NotificationItemSchema(BaseModel):
    notification_id: int
    type: str
    title: str
    message: str

    family_id: int
    target_user_id: Optional[int] = None     # 개인 알림이면 값 있음, broadcast면 None

    related_pet: Optional[RelatedPetSchema] = None
    related_user: Optional[RelatedUserSchema] = None

    is_read_by_me: bool
    is_me: bool

    read_count: int
    unread_count: int

    created_at: datetime
    display_time: str
    display_type_label: str

    class Config:
        from_attributes = True


# -------------------------
# List Response
# -------------------------
class NotificationListResponse(BaseModel):
    success: bool
    status: int

    notifications: List[NotificationItemSchema]

    page: int
    size: int
    total_count: int

    timeStamp: str
    path: str
