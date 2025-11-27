# app/schemas/notifications/common_action_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationActionItem(BaseModel):
    notification_id: int
    type: str
    title: str
    message: str

    family_id: Optional[int] = None
    target_user_id: Optional[int] = None
    related_pet_id: Optional[int] = None
    related_user_id: Optional[int] = None

    created_at: datetime


class NotificationActionResponse(BaseModel):
    success: bool
    status: int
    notification: NotificationActionItem
    timeStamp: str
    path: str
