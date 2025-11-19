from pydantic import BaseModel, Field
from typing import List, Optional


class UploadedBy(BaseModel):
    """업로드한 사용자 정보"""
    user_id: int = Field(..., description="사용자 ID")
    nickname: Optional[str] = Field(None, description="닉네임")


class PhotoListItem(BaseModel):
    """사진 목록 항목"""
    photo_id: int = Field(..., description="사진 ID")
    walk_id: int = Field(..., description="산책 ID")
    image_url: str = Field(..., description="이미지 URL")
    uploaded_by: UploadedBy = Field(..., description="업로드한 사용자 정보")
    caption: Optional[str] = Field(None, description="사진 설명")
    walk_date: Optional[str] = Field(None, description="산책 날짜 (YYYY-MM-DD)")
    walk_start_time: Optional[str] = Field(None, description="산책 시작 시간 (ISO 형식)")
    created_at: Optional[str] = Field(None, description="생성 시간 (ISO 형식)")


class PhotoListResponse(BaseModel):
    """사진 목록 조회 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    pet_id: int = Field(..., description="반려동물 ID")
    photos: List[PhotoListItem] = Field(default_factory=list, description="사진 목록")
    page: int = Field(..., description="현재 페이지 번호 (0부터 시작)")
    size: int = Field(..., description="페이지 크기")
    total_count: int = Field(..., description="전체 사진 개수")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
