from pydantic import BaseModel, Field
from typing import List, Optional


class MyPetItem(BaseModel):
    """내 반려동물 항목"""
    pet_id: int = Field(..., description="반려동물 ID")
    family_id: int = Field(..., description="가족 ID")
    family_name: Optional[str] = Field(None, description="가족 이름")
    owner_id: int = Field(..., description="소유자 ID")
    is_owner: bool = Field(..., description="소유자 여부")
    name: str = Field(..., description="반려동물 이름")
    breed: Optional[str] = Field(None, description="품종")
    age: Optional[int] = Field(None, description="나이")
    weight: Optional[float] = Field(None, description="몸무게 (kg)")
    gender: Optional[str] = Field(None, description="성별 (M, F, Unknown)")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    created_at: Optional[str] = Field(None, description="생성 시간 (ISO 형식)")
    updated_at: Optional[str] = Field(None, description="업데이트 시간 (ISO 형식)")


class MyPetsResponse(BaseModel):
    """내 반려동물 목록 조회 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    pets: List[MyPetItem] = Field(default_factory=list, description="반려동물 목록")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
