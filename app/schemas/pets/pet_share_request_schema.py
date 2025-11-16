from pydantic import BaseModel, Field
from typing import Optional


class PetShareRequestCreate(BaseModel):
    pet_search_id: str = Field(..., description="초대코드(반려동물 검색 ID)")
    message: Optional[None | str] = None


class PetShareApproveRequest(BaseModel):
    status: str = Field(..., description="APPROVED 또는 REJECTED")


class ShareRequestInfo(BaseModel):
    id: int
    pet_id: int
    requester_id: int
    status: str
    message: Optional[str] = None
    created_at: Optional[str] = None
    responded_at: Optional[str] = None


class PetBrief(BaseModel):
    pet_id: int
    name: Optional[str] = None
    breed: Optional[str] = None
    image_url: Optional[str] = None


class OwnerBrief(BaseModel):
    user_id: int
    nickname: Optional[str] = None


class FamilyMemberInfo(BaseModel):
    id: int
    family_id: int
    user_id: int
    role: str
    joined_at: Optional[str] = None


class PetShareRequestResponse(BaseModel):
    success: bool = True
    status: int = 201
    share_request: ShareRequestInfo
    pet: PetBrief
    owner: OwnerBrief
    timeStamp: str
    path: str


class PetShareApproveResponse(BaseModel):
    success: bool = True
    status: int = 200
    share_request: ShareRequestInfo
    member_added: bool
    family_member: Optional[FamilyMemberInfo] = None
    timeStamp: str
    path: str
