from fastapi import APIRouter, Depends, Request, Query, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.users.service.family_member_service import FamilyMemberService
from app.schemas.users.family_member_schema import FamilyMembersResponse

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

@router.get(
    "/family-members",
    response_model=FamilyMembersResponse,
    summary="가족 구성원 조회",
    description="특정 가족(family_id)에 속한 모든 사용자 목록을 조회합니다.",
)
async def get_family_members(
    request: Request,
    family_id: int = Query(..., description="조회할 가족 ID"),
    authorization: str | None = Header(None, description="Firebase ID Token (Bearer <token>)"),
    db: Session = Depends(get_db),
):
    service = FamilyMemberService(db)
    return service.get_family_members(request, family_id, authorization)