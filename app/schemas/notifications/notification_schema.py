# app/schemas/notifications/notification_schema.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


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
    target_user_id: Optional[int] = None     # 가족 알림이면 None

    related_pet: Optional[RelatedPetSchema] = None
    related_user: Optional[RelatedUserSchema] = None

    related_request_id: Optional[int] = None   # ⭐ 공유 요청 알림일 때 필요
    related_lat: Optional[float] = None        # ⭐ GPS 기반 알림
    related_lng: Optional[float] = None

    is_read_by_me: bool
    is_me: bool

    # 읽음/안읽음 카운트
    read_count: int
    unread_count: int

    # 보낸 사람 프로필 (UI 표시용)
    sender_profile_img_url: Optional[str] = None
    sender_nickname: Optional[str] = None

    # UI 표시용
    display_time: str
    display_type_label: str
    display_read_text: str

    created_at: datetime

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
