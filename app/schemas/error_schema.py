from pydantic import BaseModel, Field
from datetime import datetime

class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = Field(False, description="성공 여부 (항상 false)")
    status: int = Field(..., description="HTTP 상태 코드")
    code: str = Field(..., description="에러 코드")
    reason: str = Field(..., description="에러 사유")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
