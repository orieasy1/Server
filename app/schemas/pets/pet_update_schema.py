from pydantic import BaseModel, Field
from typing import Optional

class PetUpdateRequest(BaseModel):
    """반려동물 정보 수정 요청"""
    name: Optional[str] = Field(None, description="반려동물 이름")
    breed: Optional[str] = Field(None, description="품종")
    age: Optional[int] = Field(None, description="나이(년)")
    weight: Optional[float] = Field(None, description="몸무게(kg)")
    gender: Optional[str] = Field(None, description="성별: 'M' | 'F' | 'Unknown'")
    disease: Optional[str] = Field(
        None,
        description="기저 질환 정보 (예: 심장병, 관절염). 없으면 null"
    )
    
class PetUpdateResponse(BaseModel):
    """반려동물 정보 수정 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    pet: dict = Field(..., description="수정된 반려동물 정보")
    recommendation: Optional[dict] = Field(None, description="추천 산책 정보 (업데이트된 경우)")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
