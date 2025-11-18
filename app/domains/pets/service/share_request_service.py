from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.models.pet import Pet
from app.models.notification import Notification, NotificationType
from app.models.pet_share_request import RequestStatus

# 새로운 Repo 구조
from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.pets.repository.family_repository import FamilyRepository
from app.domains.pets.repository.pet_share_repository import PetShareRepository

from app.schemas.pets.pet_share_request_schema import (
    PetShareRequestCreate,
    PetShareApproveRequest,
)


class PetShareRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.share_repo = PetShareRepository(db)
        self.family_repo = FamilyRepository(db)   # 🔥 FamilyRepository 사용!

    # ---------------------------------------------------------
    # 1) 공유 요청 생성
    # ---------------------------------------------------------
    def create_request(
        self,
        request: Request,
        authorization: Optional[str],
        pet_search_id: str,
        body: PetShareRequestCreate,
    ):
        path = request.url.path

        # 1) Auth
        if authorization is None:
            return error_response(401, "PET_SHARE_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_SHARE_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "PET_SHARE_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)

        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "PET_SHARE_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 2) User 조회
        user: User | None = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_SHARE_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 3) pet_search_id
        if not pet_search_id:
            return error_response(400, "PET_SHARE_400_1", "pet_search_id는 필수 값입니다.", path)

        # 4) Pet 조회
        pet = self.pet_repo.get_by_search_id(pet_search_id)
        if not pet:
            return error_response(
                404, "PET_SHARE_404_2",
                "해당 초대코드에 해당하는 반려동물을 찾을 수 없습니다.",
                path
            )

        # 5) 이미 family 구성원인지 확인 (FamilyRepository 사용)
        if self.family_repo.is_member(user.user_id, pet.family_id):
            return error_response(
                409, "PET_SHARE_409_1",
                "이미 해당 반려동물이 속한 가족 그룹의 구성원입니다.",
                path
            )

        # 6) 이미 PENDING 요청 존재?
        if self.share_repo.exists_pending_request(pet.pet_id, user.user_id):
            return error_response(
                409, "PET_SHARE_409_2",
                "이미 처리 대기 중인 공유 요청이 존재합니다.",
                path
            )

        # 7) 요청 생성
        try:
            req = self.share_repo.create_request(
                pet_id=pet.pet_id,
                requester_id=user.user_id,
                message=body.message if body else None,
            )
            self.db.commit()
            self.db.refresh(req)
        except Exception as e:
            print("PET_SHARE_CREATE_ERROR:", e)
            self.db.rollback()
            return error_response(
                500, "PET_SHARE_500_1",
                "반려동물 공유 요청을 생성하는 중 오류가 발생했습니다.",
                path
            )
        
        # 7-1) 🔔 공유 요청 알림
        owner = self.db.get(User, pet.owner_id)
        if owner:
            self._create_notification(
                family_id=pet.family_id,
                target_user_id=owner.user_id,
                type=NotificationType.REQUEST,
                title="반려동물 공유 요청",
                message=f"{user.nickname}님이 {pet.name} 공유 요청을 보냈습니다.",
                pet_id=pet.pet_id,
                user_id=user.user_id
            )

        # 8) Owner 정보
        owner: User | None = self.db.get(User, pet.owner_id)

        response = {
            "success": True,
            "status": 201,
            "share_request": {
                "id": req.request_id,
                "pet_id": req.pet_id,
                "requester_id": req.requester_id,
                "status": req.status.value,
                "message": req.message,
                "created_at": req.created_at.isoformat(),
                "responded_at": None,
            },
            "pet": {
                "pet_id": pet.pet_id,
                "name": pet.name,
                "breed": pet.breed,
                "image_url": pet.image_url,
            },
            "owner": {
                "user_id": owner.user_id if owner else pet.owner_id,
                "nickname": owner.nickname if owner else None,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }

        return JSONResponse(status_code=201, content=jsonable_encoder(response))

    # ---------------------------------------------------------
    # 2) 공유 요청 승인 / 거절
    # ---------------------------------------------------------
    def approve_request(
        self,
        request: Request,
        authorization: Optional[str],
        request_id: int,
        body: PetShareApproveRequest,
    ):
        path = request.url.path

        # 1) Auth
        if authorization is None:
            return error_response(401, "PET_SHARE_APPROVE_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_SHARE_APPROVE_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "PET_SHARE_APPROVE_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 2) User 조회
        user: User | None = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_SHARE_APPROVE_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 3) Body 검증
        if not body or not body.status:
            return error_response(400, "PET_SHARE_APPROVE_400_1", "status 필드는 필수입니다.", path)

        status_upper = body.status.upper()
        if status_upper not in ("APPROVED", "REJECTED"):
            return error_response(400, "PET_SHARE_APPROVE_400_2", "status는 'APPROVED' 또는 'REJECTED'만 허용됩니다.", path)

        new_status = RequestStatus.APPROVED if status_upper == "APPROVED" else RequestStatus.REJECTED

        # 4) 요청 조회
        req = self.share_repo.get_request_by_id(request_id)
        if not req:
            return error_response(404, "PET_SHARE_APPROVE_404_2", "해당 공유 요청을 찾을 수 없습니다.", path)

        # 5) pet 조회
        pet = self.db.get(Pet, req.pet_id)
        if not pet:
            return error_response(404, "PET_SHARE_APPROVE_404_3", "공유 요청에 연결된 반려동물을 찾을 수 없습니다.", path)

        # 6) owner만 승인 가능
        if pet.owner_id != user.user_id:
            return error_response(
                403, "PET_SHARE_APPROVE_403_1",
                "해당 반려동물의 소유자만 공유 요청을 승인하거나 거절할 수 있습니다.",
                path
            )

        # 7) 이미 처리됨?
        if req.status in (RequestStatus.APPROVED, RequestStatus.REJECTED):
            return error_response(
                409, "PET_SHARE_APPROVE_409_1",
                "이미 처리된 공유 요청입니다.",
                path
            )

        member_added = False
        created_member = None

        try:
            # 응답 상태 업데이트
            req.status = new_status
            req.responded_at = datetime.utcnow()

            # APPROVED → family_members 추가
            if new_status == RequestStatus.APPROVED:
                if not self.family_repo.is_member(req.requester_id, pet.family_id):
                    created_member = self.family_repo.create_member(
                        family_id=pet.family_id,
                        user_id=req.requester_id
                    )
                    member_added = True

            self.db.commit()
            self.db.refresh(req)
            if created_member:
                self.db.refresh(created_member)

        except Exception as e:
            print("PET_SHARE_APPROVE_ERROR:", e)
            self.db.rollback()
            return error_response(
                500, "PET_SHARE_APPROVE_500_1",
                "반려동물 공유 요청을 처리하는 중 오류가 발생했습니다.",
                path
            )
        
        # 8) 🔔 승인/거절 알림
        requester = self.db.get(User, req.requester_id)

        if requester:
            if new_status == RequestStatus.APPROVED:
                self._create_notification(
                    family_id=pet.family_id,
                    target_user_id=requester.user_id,
                    type=NotificationType.REQUEST,
                    title="공유 요청 승인됨",
                    message=f"{pet.name} 공유 요청이 승인되었습니다!",
                    pet_id=pet.pet_id,
                    user_id=requester.user_id,
                )
            else:
                self._create_notification(
                    family_id=pet.family_id,
                    target_user_id=requester.user_id,
                    type=NotificationType.REQUEST,
                    title="공유 요청 거절됨",
                    message=f"{pet.name} 공유 요청이 거절되었습니다.",
                    pet_id=pet.pet_id,
                    user_id=requester.user_id,
                )

        # 응답
        response = {
            "success": True,
            "status": 200,
            "share_request": {
                "id": req.request_id,
                "pet_id": req.pet_id,
                "requester_id": req.requester_id,
                "status": req.status.value,
                "message": req.message,
                "created_at": req.created_at.isoformat(),
                "responded_at": req.responded_at.isoformat(),
            },
            "member_added": member_added,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }

        if member_added and created_member:
            response["family_member"] = {
                "id": created_member.member_id,
                "family_id": created_member.family_id,
                "user_id": created_member.user_id,
                "role": created_member.role.value,
                "joined_at": created_member.joined_at.isoformat(),
            }

        return JSONResponse(status_code=200, content=jsonable_encoder(response))

    def _create_notification(self, family_id, target_user_id, type, title, message, pet_id, user_id):
        try:
            notification = Notification(
                family_id=family_id,
                target_user_id=target_user_id,
                type=type,
                title=title,
                message=message,
                related_pet_id=pet_id,
                related_user_id=user_id,
            )
            self.db.add(notification)
            self.db.commit()
        except Exception as e:
            print("NOTIFICATION_ERROR:", e)
            self.db.rollback()
