from pydantic import BaseModel, Field
from typing import Optional, List


class PetBrief(BaseModel):
    """반려동물 간략 정보"""
    pet_id: int = Field(..., description="반려동물 ID")
    name: Optional[str] = Field(None, description="반려동물 이름")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    family_id: Optional[int] = Field(None, description="가족 ID")
    family_name: Optional[str] = Field(None, description="가족 이름")


class WalkerBrief(BaseModel):
    """산책한 사용자 간략 정보"""
    user_id: int = Field(..., description="사용자 ID")
    nickname: Optional[str] = Field(None, description="닉네임")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")


class RouteData(BaseModel):
    """경로 데이터"""
    polyline: Optional[str] = Field(None, description="인코딩된 폴리라인 문자열")
    points_count: Optional[int] = Field(None, description="포인트 개수")


class TrackPoint(BaseModel):
    """산책 위치 포인트"""
    point_id: int = Field(..., description="포인트 ID")
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")
    timestamp: str = Field(..., description="타임스탬프 (ISO 형식)")


class PhotoItem(BaseModel):
    """사진 항목"""
    photo_id: int = Field(..., description="사진 ID")
    image_url: str = Field(..., description="이미지 URL")
    uploaded_by: int = Field(..., description="업로드한 사용자 ID")
    caption: Optional[str] = Field(None, description="사진 설명")
    created_at: Optional[str] = Field(None, description="생성 시간 (ISO 형식)")


class WalkDetail(BaseModel):
    """산책 상세 정보"""
    walk_id: int = Field(..., description="산책 ID")
    pet: PetBrief = Field(..., description="반려동물 정보")
    walker: WalkerBrief = Field(..., description="산책한 사용자 정보")
    start_time: str = Field(..., description="시작 시간 (ISO 형식)")
    end_time: Optional[str] = Field(None, description="종료 시간 (ISO 형식)")
    duration_min: Optional[int] = Field(None, description="산책 시간 (분)")
    distance_km: Optional[float] = Field(None, description="산책 거리 (km)")
    calories: Optional[float] = Field(None, description="소모 칼로리")
    weather_status: Optional[str] = Field(None, description="날씨 상태")
    weather_temp_c: Optional[float] = Field(None, description="기온 (℃)")
    route_data: Optional[RouteData] = Field(None, description="경로 데이터")
    points: Optional[List[TrackPoint]] = Field(None, description="산책 위치 포인트 목록")
    photos: List[PhotoItem] = Field(default_factory=list, description="사진 목록")


class WalkDetailResponse(BaseModel):
    """산책 상세 조회 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    walk: WalkDetail = Field(..., description="산책 상세 정보")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
