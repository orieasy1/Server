from pydantic import BaseModel, Field
from typing import List, Optional


class WalkItem(BaseModel):
    """산책 항목"""
    walk_id: int = Field(..., description="산책 ID")
    pet_id: int = Field(..., description="반려동물 ID")
    user_id: int = Field(..., description="사용자 ID")
    start_time: str = Field(..., description="시작 시간 (ISO 형식)")
    end_time: Optional[str] = Field(None, description="종료 시간 (ISO 형식)")
    duration_min: Optional[int] = Field(None, description="산책 시간 (분)")
    distance_km: Optional[float] = Field(None, description="산책 거리 (km)")
    calories: Optional[float] = Field(None, description="소모 칼로리")
    weather_status: Optional[str] = Field(None, description="날씨 상태")
    weather_temp_c: Optional[float] = Field(None, description="기온 (℃)")


class WalkListResponse(BaseModel):
    """산책 목록 조회 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    walks: List[WalkItem] = Field(default_factory=list, description="산책 목록")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
