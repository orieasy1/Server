from pydantic import BaseModel, Field
from typing import Optional


class LoginUser(BaseModel):
    """로그인한 사용자 정보"""
    user_id: int = Field(..., description="사용자 ID")
    firebase_uid: str = Field(..., description="Firebase UID")
    nickname: str = Field(..., description="닉네임")
    email: Optional[str] = Field(None, description="이메일")
    phone: Optional[str] = Field(None, description="전화번호")
    profile_img_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    provider: str = Field(..., description="인증 제공자 (google, apple 등)")

    class Config:
        orm_mode = True


class LoginResponse(BaseModel):
    """로그인 응답"""
    is_new_user: bool = Field(..., description="신규 사용자 여부")
    user: LoginUser = Field(..., description="사용자 정보")
