# app/domains/pets/service/share_request_service.py

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

from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.pets.repository.family_repository import FamilyRepository
from app.domains.pets.repository.pet_share_repository import PetShareRepository


class PetShareRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.share_repo = PetShareRepository(db)
        self.family_repo = FamilyRepository(db)

    # ---------------------------------------------------------
    # 1) 공유 요청 생성
    # ---------------------------------------------------------
    def create_request(
        self,
        request: Request,
        authorization: Optional[str],
        pet_search_id: str,
    ):
        path = request.url.path

        # 1) Auth
        if not authorization or not authorization.startswith("Bearer "):
            return error_response(401, "PET_SHARE_401_1", "Authorization 헤더가 필요합니다.", path)

        token = authorization.split(" ")[1]
        decoded = verify_firebase_token(token)
        if decoded is None:
            return error_response(401, "PET_SHARE_401_2", "유효하지 않은 토큰입니다.", path)

        firebase_uid = decoded["uid"]

        # 2) User 조회
        user = self.db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            return error_response(404, "PET_SHARE_404_1", "사용자를 찾을 수 없습니다.", path)

        # 3) Pet 조회
        pet = self.pet_repo.get_by_search_id(pet_search_id)
        if not pet:
            return error_response(404, "PET_SHARE_404_2", "해당 초대코드의 반려동물이 없습니다.", path)

        # 4) 이미 가족 구성원인지 검사
        if self.family_repo.is_member(user.user_id, pet.family_id):
            return error_response(409, "PET_SHARE_409_1", "이미 가족 구성원입니다.", path)

        # 5) 요청 중복 확인
        if self.share_repo.exists_pending_request(pet.pet_id, user.user_id):
            return error_response(409, "PET_SHARE_409_2", "이미 처리 대기 중인 요청이 존재합니다.", path)

        # 6) 요청 생성
        try:
            req = self.share_repo.create_request(
                pet_id=pet.pet_id,
                requester_id=user.user_id,
            )
            self.db.commit()
            self.db.refresh(req)
        except Exception:
            self.db.rollback()
            return error_response(500, "PET_SHARE_500_1", "요청 생성 중 오류가 발생했습니다.", path)

        # 7️⃣ Owner + 기존 Family Member 에게 알림 생성
        family_members = self.family_repo.get_members(pet.family_id)
        for m in family_members:
            self._create_notification(
                family_id=pet.family_id,
                target_user_id=m.user_id,
                type=NotificationType.REQUEST,
                title="반려동물 공유 요청",
                message=f"{user.nickname}님이 {pet.name} 공유 요청을 보냈습니다.",
                pet_id=pet.pet_id,
                user_id=user.user_id,
                request_id=req.request_id,
            )

        # 응답
        response = {
            "success": True,
            "status": 201,
            "share_request": {
                "id": req.request_id,
                "pet_id": req.pet_id,
                "requester_id": req.requester_id,
                "status": req.status.value,
                "created_at": req.created_at.isoformat(),
            },
            "pet": {
                "pet_id": pet.pet_id,
                "name": pet.name,
                "breed": pet.breed,
                "image_url": pet.image_url,
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
        body,
    ):
        path = request.url.path

        # 1) Auth
        if not authorization or not authorization.startswith("Bearer "):
            return error_response(401, "PET_SHARE_APPROVE_401_1", "Authorization 필요", path)

        token = authorization.split(" ")[1]
        decoded = verify_firebase_token(token)
        if decoded is None:
            return error_response(401, "PET_SHARE_APPROVE_401_2", "유효하지 않은 토큰입니다.", path)

        firebase_uid = decoded["uid"]

        # 2) User 조회
        user = self.db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            return error_response(404, "PET_SHARE_APPROVE_404_1", "사용자를 찾을 수 없습니다.", path)

        # 3) Body 검증
        if not body or not body.status:
            return error_response(400, "PET_SHARE_APPROVE_400_1", "status 필수", path)

        new_status = RequestStatus.APPROVED if body.status.upper() == "APPROVED" else RequestStatus.REJECTED

        # 4) 요청 조회
        req = self.share_repo.get_request_by_id(request_id)
        if not req:
            return error_response(404, "PET_SHARE_APPROVE_404_2", "요청을 찾을 수 없습니다.", path)

        pet = self.db.get(Pet, req.pet_id)

        # 5) owner만 승인 가능
        if pet.owner_id != user.user_id:
            return error_response(403, "PET_SHARE_APPROVE_403_1", "owner 권한 없음", path)

        # 6) 이미 처리됨
        if req.status != RequestStatus.PENDING:
            return error_response(409, "PET_SHARE_APPROVE_409_1", "이미 처리됨", path)

        # 7) 승인 처리
        try:
            req.status = new_status
            req.responded_at = datetime.utcnow()

            created_member = None
            if new_status == RequestStatus.APPROVED:
                created_member = self.family_repo.create_member(
                    family_id=pet.family_id,
                    user_id=req.requester_id
                )

            self.db.commit()
            self.db.refresh(req)
        except Exception:
            self.db.rollback()
            return error_response(500, "PET_SHARE_APPROVE_500_1", "처리 중 오류", path)

        # 8️⃣ 결과 알림 (기존 Family Member + Owner → 모두 받음, 신청자는 제외)
        family_members = self.family_repo.get_members(pet.family_id)

        notif_type = (
            NotificationType.INVITE_ACCEPTED if new_status == RequestStatus.APPROVED
            else NotificationType.INVITE_REJECTED
        )
        notif_title = "공유 요청 승인됨" if new_status == RequestStatus.APPROVED else "공유 요청 거절됨"
        notif_msg = (
            f"{pet.name} 공유 요청이 승인되었습니다!"
            if new_status == RequestStatus.APPROVED
            else f"{pet.name} 공유 요청이 거절되었습니다."
        )

        for m in family_members:
            self._create_notification(
                family_id=pet.family_id,
                target_user_id=m.user_id,
                type=notif_type,
                title=notif_title,
                message=notif_msg,
                pet_id=pet.pet_id,
                user_id=user.user_id,
                request_id=req.request_id,
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
                "created_at": req.created_at.isoformat(),
                "responded_at": req.responded_at.isoformat(),
            },
            "member_added": created_member is not None,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }

        return JSONResponse(status_code=200, content=jsonable_encoder(response))

    # ---------------------------------------------------------
    # 3) 알림 생성 함수
    # ---------------------------------------------------------
    def _create_notification(
        self,
        family_id: int,
        target_user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        pet_id: int,
        user_id: int,
        request_id: Optional[int] = None,
    ):
        try:
            notification = Notification(
                family_id=family_id,
                target_user_id=target_user_id,
                type=type,
                title=title,
                message=message,
                related_pet_id=pet_id,
                related_user_id=user_id,
                related_request_id=request_id,
            )
            self.db.add(notification)
            self.db.commit()
        except Exception as e:
            print("NOTIFICATION_ERROR:", e)
            self.db.rollback()

    def get_my_requests(
        self,
        request: Request,
        authorization: Optional[str],
        status: Optional[str],
        page: int,
        size: int,
    ):
        path = request.url.path

        # 1) Auth
        if not authorization or not authorization.startswith("Bearer "):
            return error_response(401, "REQ_LIST_401", "Authorization 필요", path)

        token = authorization.split(" ")[1]
        decoded = verify_firebase_token(token)
        if decoded is None:
            return error_response(401, "REQ_LIST_401_2", "유효하지 않은 토큰입니다.", path)

        firebase_uid = decoded["uid"]

        # 2) User 조회
        user = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "REQ_LIST_404_1", "사용자를 찾을 수 없습니다.", path)

        # 3) Status 파싱
        parsed_status = None
        if status:
            try:
                parsed_status = RequestStatus(status.upper())
            except Exception:
                return error_response(400, "REQ_LIST_400", "status 값이 잘못되었습니다.", path)

        # 4) Repository 조회
        items, total = self.share_repo.get_requests_by_user(
            requester_id=user.user_id,
            status=parsed_status,
            page=page,
            size=size,
        )

        # 5) 응답 조립
        results = []
        for req in items:
            pet = self.db.get(Pet, req.pet_id)

            results.append({
                "request_id": req.request_id,
                "pet_id": pet.pet_id,
                "pet_name": pet.name,
                "pet_image_url": pet.image_url,
                "status": req.status.value,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "responded_at": req.responded_at.isoformat() if req.responded_at else None,
            })

        return {
            "success": True,
            "status": 200,
            "requests": results,
            "page": page,
            "size": size,
            "total_count": total,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }
