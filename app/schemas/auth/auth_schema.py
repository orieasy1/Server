from pydantic import BaseModel
from typing import Optional


class LoginUser(BaseModel):
    user_id: int
    firebase_uid: str
    nickname: str
    email: Optional[str]
    phone: Optional[str]
    profile_img_url: Optional[str]
    provider: str

    class Config:
        orm_mode = True


class LoginResponse(BaseModel):
    is_new_user: bool
    user: LoginUser
