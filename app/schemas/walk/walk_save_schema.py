from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RoutePointDto(BaseModel):
    """경로 포인트 DTO"""
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    timestamp: str = Field(..., description="타임스탬프 (ISO 8601 형식: YYYY-MM-DDTHH:mm:ss)")


class WalkSaveRequest(BaseModel):
    """산책 저장 요청"""
    pet_id: int = Field(..., description="반려동물 ID")
    start_time: str = Field(..., description="산책 시작 시간 (ISO 8601 형식: YYYY-MM-DDTHH:mm:ss)")
    end_time: str = Field(..., description="산책 종료 시간 (ISO 8601 형식: YYYY-MM-DDTHH:mm:ss)")
    duration_min: int = Field(..., description="소요 시간 (분)")
    distance_km: float = Field(..., description="이동 거리 (킬로미터)")
    calories: Optional[float] = Field(None, description="소모 칼로리")
    weather_status: Optional[str] = Field(None, description="날씨 상태 (예: '맑음', '흐림')")
    weather_temp_c: Optional[float] = Field(None, description="날씨 온도 (섭씨)")
    thumbnail_image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    route_points: Optional[List[RoutePointDto]] = Field(None, description="경로 포인트 목록")


class WalkSaveDetail(BaseModel):
    """산책 저장 상세 정보"""
    walk_id: int = Field(..., description="산책 ID")
    pet_id: int = Field(..., description="반려동물 ID")
    user_id: int = Field(..., description="사용자 ID")
    start_time: str = Field(..., description="시작 시간 (ISO 형식)")
    end_time: str = Field(..., description="종료 시간 (ISO 형식)")
    duration_min: int = Field(..., description="산책 시간 (분)")
    distance_km: float = Field(..., description="산책 거리 (km)")
    calories: Optional[float] = Field(None, description="소모 칼로리")
    weather_status: Optional[str] = Field(None, description="날씨 상태")
    weather_temp_c: Optional[float] = Field(None, description="기온 (℃)")
    thumbnail_image_url: Optional[str] = Field(None, description="대표 이미지 URL")


class WalkSaveResponse(BaseModel):
    """산책 저장 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    walk: WalkSaveDetail = Field(..., description="산책 정보")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")


