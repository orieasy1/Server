from pydantic import BaseModel, Field
from typing import Optional

class UserUpdateRequest(BaseModel):
    """사용자 정보 수정 요청"""
    nickname: Optional[str] = Field(None, description="닉네임")
    phone: Optional[str] = Field(None, description="전화번호")
