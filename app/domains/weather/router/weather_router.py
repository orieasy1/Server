from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
import httpx
import os

from app.core.config import settings

router = APIRouter(
    prefix="/api/v1/weather",
    tags=["Weather"]
)


@router.get(
    "/current",
    summary="현재 날씨 조회",
    description="OpenWeatherMap API를 통해 현재 날씨 정보를 조회합니다.",
    status_code=200,
    responses={
        400: {"description": "잘못된 요청 (위도/경도 파라미터 누락 또는 범위 초과)"},
        500: {"description": "서버 내부 오류"},
        502: {"description": "외부 날씨 서비스 응답 오류"},
        503: {"description": "외부 날씨 서비스 타임아웃 또는 이용 불가"},
    },
)
async def get_current_weather(
    request: Request,
    lat: float = Query(..., description="위도", ge=-90, le=90),
    lon: float = Query(..., description="경도", ge=-180, le=180),
):
    """
    OpenWeatherMap API를 호출하여 현재 날씨 정보를 조회합니다.
    응답은 OpenWeatherMap API의 원본 응답을 그대로 반환합니다.
    """
    # 환경 변수에서 API 키 가져오기
    api_key = settings.OPENWEATHER_API_KEY
    
    if not api_key or api_key == "dummy_key":
        raise HTTPException(
            status_code=500,
            detail="OpenWeatherMap API key is not configured"
        )
    
    # OpenWeatherMap API 호출
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric',
        'lang': 'kr'
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if 500 <= e.response.status_code < 600:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch weather data from external service"
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to fetch weather data: {e.response.text}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=503,
            detail="Weather service timeout. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


