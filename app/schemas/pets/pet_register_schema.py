from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PetRegisterRequest(BaseModel):
    """반려동물 등록 요청"""
    name: str = Field(..., description="반려동물 이름")
    breed: Optional[str] = Field(None, description="품종")
    age: Optional[int] = Field(None, description="나이 (년)")
    weight: Optional[float] = Field(None, description="몸무게 (kg)")
    gender: Optional[str] = Field(None, description="성별 (M, F, Unknown)")
    pet_search_id: str = Field(..., description="초대 코드 (영문+숫자 8자리)")
    image_url: Optional[str] = Field(None, description="이미지 URL (Firebase Storage 등)")
    voice_url: Optional[str] = Field(None, description="음성 녹음 URL (Firebase Storage 등)")
    disease: Optional[str] = Field(
        None,
        description="기저 질환 정보 (예: 심장병, 관절염). 없으면 null"
    )


class PetInfo(BaseModel):
    pet_id: int
    family_id: int
    owner_id: int
    pet_search_id: str
    name: str
    breed: Optional[str]
    age: Optional[int]
    weight: Optional[float]
    gender: Optional[str]
    disease: Optional[str]
    image_url: Optional[str]
    voice_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class FamilyInfo(BaseModel):
    id: int
    family_name: str
    created_at: datetime
    updated_at: Optional[datetime]


class OwnerMemberInfo(BaseModel):
    id: int
    family_id: int
    user_id: int
    role: str
    joined_at: datetime


class RecommendationInfo(BaseModel):
    rec_id: int
    pet_id: int
    min_walks: int
    min_minutes: int
    min_distance_km: float
    recommended_walks: int
    recommended_minutes: int
    recommended_distance_km: float
    max_walks: int
    max_minutes: int
    max_distance_km: float
    generated_by: str
    updated_at: datetime


class PetRegisterResponse(BaseModel):
    success: bool
    status: int
    pet: PetInfo
    family: FamilyInfo
    owner_member: OwnerMemberInfo
    recommendation: RecommendationInfo
    timeStamp: datetime
    path: str
