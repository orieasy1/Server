from pydantic import BaseModel, Field

class PetImageResponse(BaseModel):
    """반려동물 이미지 업로드 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    image_url: str = Field(..., description="업로드된 이미지 URL")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
