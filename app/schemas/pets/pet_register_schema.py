from pydantic import BaseModel, Field
from typing import Optional


class PetRegisterRequest(BaseModel):
    name: str = Field(..., description="반려동물 이름")
    breed: Optional[str] = Field(None, description="품종")
    age: Optional[int] = Field(None, description="나이")
    weight: Optional[float] = Field(None, description="몸무게 (kg)")
    gender: Optional[str] = Field(None, description="M, F, Unknown")
    pet_search_id: str = Field(..., description="초대 코드 (영문+숫자 8자리)")
    image_url: Optional[str] = Field(None, description="이미지 URL (Firebase Storage 등)")
