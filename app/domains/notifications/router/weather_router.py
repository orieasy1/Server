# app/domains/notifications/router/weather_router.py

from fastapi import APIRouter, Request, Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.notifications.service.weather_service import WeatherService
from app.schemas.notifications.weather_schema import WeatherRecommendationRequest
from app.schemas.notifications.common_action_schema import NotificationActionResponse

router = APIRouter(
    prefix="/api/v1/notifications/weather",
    tags=["Weather Notification"]
)


# -----------------------------
# 1) 수동/즉시 API (사용자 요청)
# -----------------------------
@router.post(
    "/recommendation",
    response_model=NotificationActionResponse,  # ⭐ 공통 응답 스키마 적용
    summary="날씨 기반 산책 추천 생성 (개인 알림)"
)
def create_weather_recommendation(
    request: Request,
    body: WeatherRecommendationRequest,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
):
    """
    날씨 기반 산책 추천을 즉시 생성하는 API.
    - Firebase Authorization 필요
    - pet_id + 위치 좌표(lat, lng) 전달
    - 응답은 NotificationActionResponse 구조로 통일
    """
    service = WeatherService(db)
    return service.generate_weather_recommendation(
        request=request,
        authorization=authorization,
        body=body,
    )
