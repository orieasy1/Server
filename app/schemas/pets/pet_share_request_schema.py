from pydantic import BaseModel, Field
from typing import Optional


class PetShareRequestCreate(BaseModel):
    """반려동물 공유 요청 생성"""
    pet_search_id: str = Field(..., description="초대코드(반려동물 검색 ID)")
    message: Optional[str] = Field(None, description="요청 메시지")


class PetShareApproveRequest(BaseModel):
    """반려동물 공유 요청 승인/거절"""
    status: str = Field(..., description="APPROVED 또는 REJECTED")


class ShareRequestInfo(BaseModel):
    """공유 요청 정보"""
    id: int = Field(..., description="요청 ID")
    pet_id: int = Field(..., description="반려동물 ID")
    requester_id: int = Field(..., description="요청자 ID")
    status: str = Field(..., description="요청 상태 (PENDING, APPROVED, REJECTED)")
    message: Optional[str] = Field(None, description="요청 메시지")
    created_at: Optional[str] = Field(None, description="생성 시간 (ISO 형식)")
    responded_at: Optional[str] = Field(None, description="응답 시간 (ISO 형식)")


class PetBrief(BaseModel):
    """반려동물 간략 정보"""
    pet_id: int = Field(..., description="반려동물 ID")
    name: Optional[str] = Field(None, description="반려동물 이름")
    breed: Optional[str] = Field(None, description="품종")
    image_url: Optional[str] = Field(None, description="이미지 URL")


class OwnerBrief(BaseModel):
    """소유자 간략 정보"""
    user_id: int = Field(..., description="사용자 ID")
    nickname: Optional[str] = Field(None, description="닉네임")


class FamilyMemberInfo(BaseModel):
    """가족 구성원 정보"""
    id: int = Field(..., description="가족 구성원 ID")
    family_id: int = Field(..., description="가족 ID")
    user_id: int = Field(..., description="사용자 ID")
    role: str = Field(..., description="역할 (OWNER, MEMBER)")
    joined_at: Optional[str] = Field(None, description="가입 시간 (ISO 형식)")


class PetShareRequestResponse(BaseModel):
    """반려동물 공유 요청 생성 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(201, description="HTTP 상태 코드")
    share_request: ShareRequestInfo = Field(..., description="공유 요청 정보")
    pet: PetBrief = Field(..., description="반려동물 정보")
    owner: OwnerBrief = Field(..., description="소유자 정보")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")


class PetShareApproveResponse(BaseModel):
    """반려동물 공유 요청 승인/거절 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    share_request: ShareRequestInfo = Field(..., description="공유 요청 정보")
    member_added: bool = Field(..., description="구성원 추가 여부")
    family_member: Optional[FamilyMemberInfo] = Field(None, description="추가된 가족 구성원 정보")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
