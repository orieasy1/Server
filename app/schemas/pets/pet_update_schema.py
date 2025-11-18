from pydantic import BaseModel, Field
from typing import Optional

class PetUpdateRequest(BaseModel):
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
    success: bool = True
    status: int = 200
    pet: dict
    recommendation: Optional[dict] = None
    timeStamp: str
    path: str
