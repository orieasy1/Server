# app/routers/notifications.py
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.notifications.service.notification_service import NotificationService
from app.schemas.notifications.notification_schema import NotificationListResponse
from app.schemas.error_schema import ErrorResponse   # 공용 에러 스키마만 사용

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get(
    "",
    summary="알림 리스트 조회 (전체 최신순)",
    description="카카오톡처럼 전체 알림을 시간순(ASC)으로 조회합니다.",
    response_model=NotificationListResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
def get_notifications(
    request: Request,
    pet_id: int | None = None,
    page: int = 0,
    size: int = 20,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    firebase_token = None
    if authorization and authorization.startswith("Bearer "):
        firebase_token = authorization.split(" ")[1]

    service = NotificationService(db)

    return service.get_notifications(
        request=request,
        firebase_token=firebase_token,
        pet_id=pet_id,
        notif_type=type,
        page=page,
        size=size
    )


@router.patch(
    "/{notification_id}/read",
    summary="알림 읽음 처리",
    description="알림을 읽음 처리합니다."
)
def mark_notification_as_read(
    notification_id: int,
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)

    firebase_token = None
    if authorization and authorization.startswith("Bearer "):
        firebase_token = authorization.split(" ")[1]

    return service.mark_read(
        notification_id=notification_id,
        firebase_token=firebase_token,
        request=request
    )
