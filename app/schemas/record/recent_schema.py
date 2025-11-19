from pydantic import BaseModel, Field
from typing import List, Optional


class WalkerBrief(BaseModel):
    """산책한 사용자 간략 정보"""
    user_id: int = Field(..., description="사용자 ID")
    nickname: Optional[str] = Field(None, description="닉네임")


class RecentActivityItem(BaseModel):
    """최근 활동 항목"""
    walk_id: int = Field(..., description="산책 ID")
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    start_time: Optional[str] = Field(None, description="시작 시간 (ISO 형식)")
    end_time: Optional[str] = Field(None, description="종료 시간 (ISO 형식)")
    duration_min: Optional[int] = Field(None, description="산책 시간 (분)")
    distance_km: Optional[float] = Field(None, description="산책 거리 (km)")
    walker: WalkerBrief = Field(..., description="산책한 사용자 정보")
    weather_status: Optional[str] = Field(None, description="날씨 상태")
    weather_temp_c: Optional[float] = Field(None, description="기온 (℃)")


class RecentActivitiesResponse(BaseModel):
    """최근 활동 조회 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    pet_id: int = Field(..., description="반려동물 ID")
    recent_activities: List[RecentActivityItem] = Field(default_factory=list, description="최근 활동 목록 (최대 3개)")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
