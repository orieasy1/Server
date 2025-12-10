from fastapi import APIRouter, Depends, Request, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.domains.users.service.family_member_service import FamilyMemberService
from app.schemas.users.family_member_schema import FamilyMembersResponse
from app.models.family_member import FamilyMember
from app.models.user import User

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


@router.get(
    "/debug/family-fcm-tokens",
    summary="[DEBUG] 가족 멤버 FCM 토큰 상태 확인",
    description="가족 멤버들의 FCM 토큰 등록 상태를 확인합니다. (디버그용)",
)
async def debug_family_fcm_tokens(
    family_id: int = Query(..., description="조회할 가족 ID"),
    db: Session = Depends(get_db),
):
    """
    가족 멤버들의 FCM 토큰 상태를 확인하는 디버그 API.
    알림이 전송되지 않는 문제를 디버깅할 때 사용합니다.
    """
    # 가족 멤버 조회
    family_members = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id)
        .all()
    )
    
    members_info = []
    for m in family_members:
        user = db.get(User, m.user_id)
        if user:
            members_info.append({
                "user_id": user.user_id,
                "nickname": user.nickname,
                "role": m.role.value,
                "has_fcm_token": user.fcm_token is not None,
                "fcm_token_preview": user.fcm_token[:30] + "..." if user.fcm_token else None,
            })
        else:
            members_info.append({
                "user_id": m.user_id,
                "nickname": None,
                "role": m.role.value,
                "has_fcm_token": False,
                "fcm_token_preview": None,
                "error": "User not found"
            })
    
    return JSONResponse(content={
        "success": True,
        "family_id": family_id,
        "total_members": len(family_members),
        "members_with_fcm_token": sum(1 for m in members_info if m.get("has_fcm_token")),
        "members": members_info,
        "timestamp": datetime.utcnow().isoformat(),
    })