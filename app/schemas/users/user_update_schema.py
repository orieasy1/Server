from pydantic import BaseModel
from typing import Optional

class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
