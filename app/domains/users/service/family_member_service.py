from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.domains.users.repository.user_repository import UserRepository
from app.schemas.users.family_member_schema import FamilyMembersResponse, FamilyMember
from app.core.firebase import verify_firebase_token


class FamilyMemberService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_family_members(self, request: Request, family_id: int, authorization: str | None):

        path = "/api/v1/users/family-members"

        # ------------------------------
        # 0) Authorization 헤더 체크
        # ------------------------------
        if authorization is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "status": 401,
                    "code": "FAMILY_MEMBERS_401_1",
                    "reason": "Authorization 헤더가 필요합니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "status": 401,
                    "code": "FAMILY_MEMBERS_401_2",
                    "reason": "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        try:
            id_token = authorization.split(" ")[1]
        except Exception:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "status": 401,
                    "code": "FAMILY_MEMBERS_401_3",
                    "reason": "Authorization 헤더 형식이 잘못되었습니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        # ------------------------------
        # 1) Firebase 토큰 검증
        # ------------------------------
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "status": 401,
                    "code": "FAMILY_MEMBERS_401_4",
                    "reason": "유효하지 않거나 만료된 Firebase ID Token입니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        firebase_uid = decoded.get("uid")

        # ------------------------------
        # 2) DB 사용자 조회
        # ------------------------------
        user = self.user_repo.get_user_by_firebase_uid(firebase_uid)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "status": 401,
                    "code": "FAMILY_MEMBERS_401_5",
                    "reason": "해당 사용자 정보가 DB에 존재하지 않습니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        current_user_id = user.user_id

        # ------------------------------
        # 3) 유저가 속한 모든 가족 조회
        # ------------------------------
        memberships = self.user_repo.get_family_memberships(current_user_id)

        if not memberships:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "status": 403,
                    "code": "FAMILY_MEMBERS_403_2",
                    "reason": "사용자는 어떤 가족에도 속해 있지 않습니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        # 유저가 속한 family_id 리스트
        user_family_ids = {m.family_id for m in memberships}

        # ------------------------------
        # 4) 요청한 family_id 접근 권한 체크
        # ------------------------------
        if family_id not in user_family_ids:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "status": 403,
                    "code": "FAMILY_MEMBERS_403_1",
                    "reason": "해당 가족의 구성원이 아니므로 접근할 수 없습니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        # ------------------------------
        # 5) family_id의 전체 멤버 조회
        # ------------------------------
        family_members = self.user_repo.get_family_members(family_id)

        if not family_members:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "status": 404,
                    "code": "FAMILY_MEMBERS_404_1",
                    "reason": "해당 가족에 등록된 구성원이 없습니다.",
                    "timeStamp": datetime.now().isoformat(),
                    "path": path,
                },
            )

        # ------------------------------
        # 6) 응답 변환
        # ------------------------------
        member_schemas = []

        for fm in family_members:
            fm_user = self.user_repo.get_user_by_id(fm.user_id)
            if not fm_user:
                continue

            member_schemas.append(
                FamilyMember(
                    user_id=fm_user.user_id,
                    nickname=fm_user.nickname,
                    profile_img_url=fm_user.profile_img_url,
                    role=fm.role.value if hasattr(fm.role, "value") else fm.role,
                    is_myself=(fm.user_id == current_user_id),
                )
            )

        # ------------------------------
        # 7) 최종 응답 반환
        # ------------------------------
        return FamilyMembersResponse(
            success=True,
            status=200,
            family_id=family_id,
            members=member_schemas,
            total_count=len(member_schemas),
            timeStamp=datetime.now(),
            path=path,
        )
