from fastapi import APIRouter, Header, Request, Depends, Query
from typing import Optional

from app.domains.walk.service.weather_service import WeatherService
from app.schemas.walk.weather_schema import WeatherResponse
from app.domains.walk.exception import WEATHER_RESPONSES


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
    responses=WEATHER_RESPONSES,
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

