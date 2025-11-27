from fastapi import APIRouter, Request, Header, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.notifications.health_schema import HealthFeedbackRequest
from app.schemas.notifications.common_action_schema import NotificationActionResponse
from app.domains.notifications.service.health_service import HealthService

router = APIRouter(prefix="/api/v1/notifications")


@router.post(
    "/health",
    response_model=NotificationActionResponse,   # ⭐ 응답 스키마 지정
    summary="건강 피드백 생성 (개인 알림)"
)
def create_health_notification(
    request: Request,
    body: HealthFeedbackRequest,
    authorization: str = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """
    개인 건강 피드백 알림 생성 API.
    - Firebase Authorization 필요
    - pet_id만 넘기면 GPT 기반 건강 요약 생성
    - 응답은 NotificationActionResponse 공통 스키마로 통일
    """
    service = HealthService(db)
    return service.generate_health_feedback(request, authorization, body)
