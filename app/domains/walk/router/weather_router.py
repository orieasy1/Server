from fastapi import APIRouter, Header, Request, Depends, Query
from typing import Optional

from app.domains.walk.service.weather_service import WeatherService
from app.schemas.error_schema import ErrorResponse
from app.schemas.walk.weather_schema import WeatherResponse


router = APIRouter(
    prefix="/api/v1/walk",
    tags=["Walk"]
)


@router.get(
    "/weather",
    summary="날씨 정보 조회",
    description="현재 위치 기반 날씨 정보를 조회합니다. 인증은 선택사항이며, 외부 API를 통해 조회됩니다.",
    status_code=200,
    response_model=WeatherResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (위도/경도 누락 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패 (선택적)"},
        502: {"model": ErrorResponse, "description": "외부 API 게이트웨이 오류"},
        503: {"model": ErrorResponse, "description": "외부 API 서비스 불가"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def get_weather(
    request: Request,
    lat: Optional[float] = Query(None, description="위도 (-90 ~ 90)"),
    lng: Optional[float] = Query(None, description="경도 (-180 ~ 180)"),
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰 (선택적)"),
):
    """
    현재 위치 기반 날씨 정보를 조회합니다.
    
    - lat: 위도 (query parameter, 필수)
    - lng: 경도 (query parameter, 필수)
    - Authorization: 옵션 (비로그인 허용 가능)
    - 외부 API 연동 (OpenWeatherMap)
    - 캐싱 (10분 간격)
    - 외부 API 장애 시 오래된 캐시 반환 (is_stale=true)
    """
    service = WeatherService()
    return service.get_weather(
        request=request,
        authorization=authorization,
        lat=lat,
        lng=lng,
    )

