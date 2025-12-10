# app/schemas/notifications/sos_schema.py

from typing import Optional
from pydantic import BaseModel


class SosRequestSchema(BaseModel):
    """SOS 알림 요청 스키마"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    message: Optional[str] = None  # 추가 메시지 (선택)


class SosResponseSchema(BaseModel):
    """SOS 알림 응답 스키마"""
    success: bool
    status: int
    message: str
    notification_id: int
    notified_count: int  # 알림 받은 가족 수
    timeStamp: str
    path: str

