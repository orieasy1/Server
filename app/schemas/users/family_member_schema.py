from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class FamilyMember(BaseModel):
    user_id: int
    nickname: str
    profile_img_url: Optional[str]
    role: str
    is_myself: bool


class FamilyMembersResponse(BaseModel):
    success: bool
    status: int
    family_id: int
    members: List[FamilyMember]
    total_count: int
    timeStamp: datetime
    path: str
