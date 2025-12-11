from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import httpx
import os

from app.core.firebase import verify_firebase_token
from app.domains.walk.exception import walk_error
from app.domains.walk.repository.weather_repository import WeatherRepository


class WeatherService:
    def __init__(self):
        self.weather_repo = WeatherRepository()
        # OpenWeatherMap API Key (환경 변수에서 가져오기)
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def _fetch_weather_from_api(
        self, lat: float, lng: float
    ) -> dict:
        """
        OpenWeatherMap API에서 날씨 정보 조회
        실제 구현 시 환경 변수에서 API 키를 가져와야 함
        """
        if not self.api_key:
            raise Exception("OpenWeatherMap API key is not configured")

        try:
            params = {
                "lat": lat,
                "lon": lng,
                "appid": self.api_key,
                "units": "metric",  # 섭씨 온도
                "lang": "kr",  # 한국어
            }

            with httpx.Client(timeout=5.0) as client:
                response = client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

            # OpenWeatherMap 응답 파싱
            weather_main = data.get("weather", [{}])[0]
            main_data = data.get("main", {})
            wind_data = data.get("wind", {})

            # 날씨 조건 매핑
            condition_map = {
                "Clear": "맑음",
                "Clouds": "구름",
                "Rain": "비",
                "Drizzle": "이슬비",
                "Thunderstorm": "천둥번개",
                "Snow": "눈",
                "Mist": "안개",
                "Fog": "안개",
                "Haze": "연무",
            }

            condition = weather_main.get("main", "Unknown")
            condition_ko = condition_map.get(condition, condition)

            # 아이콘 매핑
            icon_code = weather_main.get("icon", "")
            icon_map = {
                "01d": "CLEAR_DAY",
                "01n": "CLEAR_NIGHT",
                "02d": "PARTLY_CLOUDY_DAY",
                "02n": "PARTLY_CLOUDY_NIGHT",
                "03d": "CLOUDY",
                "03n": "CLOUDY",
                "04d": "CLOUDY",
                "04n": "CLOUDY",
                "09d": "RAIN",
                "09n": "RAIN",
                "10d": "RAIN",
                "10n": "RAIN",
                "11d": "THUNDERSTORM",
                "11n": "THUNDERSTORM",
                "13d": "SNOW",
                "13n": "SNOW",
                "50d": "FOG",
                "50n": "FOG",
            }
            icon = icon_map.get(icon_code, "CLEAR_DAY")

            return {
                "lat": lat,
                "lng": lng,
                "condition": condition,
                "condition_ko": condition_ko,
                "icon": icon,
                "temperature_c": main_data.get("temp", 0.0),
                "feels_like_c": main_data.get("feels_like"),
                "humidity": main_data.get("humidity"),
                "wind_speed_ms": wind_data.get("speed"),
                "uvi": data.get("uvi"),  # 일부 API에서는 별도 호출 필요
                "source": "OPEN_WEATHER_MAP",
            }

        except httpx.HTTPStatusError as e:
            if 500 <= e.response.status_code < 600:
                raise Exception("EXTERNAL_API_5XX")
            raise Exception("EXTERNAL_API_ERROR")
        except httpx.TimeoutException:
            raise Exception("EXTERNAL_API_TIMEOUT")
        except Exception as e:
            if "EXTERNAL_API" in str(e):
                raise
            raise Exception("EXTERNAL_API_ERROR")

    def get_weather(
        self,
        request: Request,
        authorization: Optional[str],
        lat: Optional[float],
        lng: Optional[float],
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증 (옵션 - 요구사항에 따라)
        # ============================================
        # 주석 처리: 날씨는 비로그인도 허용할 수 있음
        # if authorization is None:
        #     return error_response(
        #         401, "WEATHER_401_1", "Authorization 헤더가 필요합니다.", path
        #     )

        # ============================================
        # 2) Query Parameter 유효성 검사
        # ============================================
        # 2-1) lat/lng 필수 체크
        if lat is None or lng is None:
            return walk_error("WEATHER_400_1", path)

        # 2-2) 위도/경도 범위 체크
        try:
            latitude = float(lat)
            longitude = float(lng)
            
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return walk_error("WEATHER_400_2", path)
        except (ValueError, TypeError):
            return walk_error("WEATHER_400_2", path)

        # ============================================
        # 3) 캐시 확인
        # ============================================
        cached_weather = self.weather_repo.get_cached_weather(latitude, longitude)
        
        if cached_weather and not cached_weather.get("is_stale", False):
            # 최신 캐시가 있으면 반환
            response_content = {
                "success": True,
                "status": 200,
                "weather": {
                    **cached_weather,
                    "fetched_at": cached_weather["fetched_at"].isoformat() if isinstance(cached_weather.get("fetched_at"), datetime) else cached_weather.get("fetched_at"),
                },
                "timeStamp": datetime.utcnow().isoformat(),
                "path": path
            }
            encoded = jsonable_encoder(response_content)
            return JSONResponse(status_code=200, content=encoded)

        # ============================================
        # 4) 외부 API 호출
        # ============================================
        try:
            weather_data = self._fetch_weather_from_api(latitude, longitude)
            weather_data["fetched_at"] = datetime.utcnow()
            weather_data["cache_age_seconds"] = 0
            weather_data["is_stale"] = False

            # 캐시 저장
            self.weather_repo.set_cached_weather(latitude, longitude, weather_data)

        except Exception as e:
            error_msg = str(e)
            
            # 오래된 캐시가 있으면 반환
            if cached_weather:
                cached_weather["is_stale"] = True
                response_content = {
                    "success": True,
                    "status": 200,
                    "weather": {
                        **cached_weather,
                        "fetched_at": cached_weather["fetched_at"].isoformat() if isinstance(cached_weather.get("fetched_at"), datetime) else cached_weather.get("fetched_at"),
                    },
                    "timeStamp": datetime.utcnow().isoformat(),
                    "path": path
                }
                encoded = jsonable_encoder(response_content)
                return JSONResponse(status_code=200, content=encoded)

            # 캐시도 없고 API 호출도 실패한 경우
            if "EXTERNAL_API_5XX" in error_msg:
                return walk_error("WEATHER_502_1", path)
            elif "EXTERNAL_API_TIMEOUT" in error_msg:
                return walk_error("WEATHER_503_1", path)
            else:
                return walk_error("WEATHER_503_1", path)

        # ============================================
        # 5) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 200,
            "weather": {
                **weather_data,
                "fetched_at": weather_data["fetched_at"].isoformat() if isinstance(weather_data.get("fetched_at"), datetime) else weather_data.get("fetched_at"),
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)

