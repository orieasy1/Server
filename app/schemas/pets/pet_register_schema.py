from pydantic import BaseModel, Field
from typing import Optional


class PetRegisterRequest(BaseModel):
    """반려동물 등록 요청"""
    name: str = Field(..., description="반려동물 이름")
    breed: Optional[str] = Field(None, description="품종")
    age: Optional[int] = Field(None, description="나이 (년)")
    weight: Optional[float] = Field(None, description="몸무게 (kg)")
    gender: Optional[str] = Field(None, description="성별 (M, F, Unknown)")
    pet_search_id: str = Field(..., description="초대 코드 (영문+숫자 8자리)")
    image_url: Optional[str] = Field(None, description="이미지 URL (Firebase Storage 등)")
    disease: Optional[str] = Field(
        None,
        description="기저 질환 정보 (예: 심장병, 관절염). 없으면 null"
    )