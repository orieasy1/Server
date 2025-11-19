from pydantic import BaseModel, Field
from datetime import datetime
from app.models.pet import PetGender

class PetResponse(BaseModel):
    """반려동물 응답"""
    pet_id: int = Field(..., description="반려동물 ID")
    family_id: int = Field(..., description="가족 ID")
    owner_id: int = Field(..., description="소유자 ID")
    pet_search_id: str = Field(..., description="반려동물 검색 ID (초대코드)")
    name: str = Field(..., description="반려동물 이름")
    breed: str | None = Field(None, description="품종")
    age: int | None = Field(None, description="나이")
    weight: float | None = Field(None, description="몸무게 (kg)")
    gender: PetGender = Field(..., description="성별")
    image_url: str | None = Field(None, description="이미지 URL")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="업데이트 시간")

    class Config:
        from_attributes = True  # ORM 모델 자동 변환
