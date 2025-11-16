from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import MemberRole
from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.pets.repository.pet_recommendation_repository import PetRecommendationRepository
from app.domains.pets.repository.pet_share_repository import PetShareRepository
from app.domains.pets.repository.family_member_repository import FamilyMemberRepository
from app.models.pet_share_request import RequestStatus
from app.schemas.pets.pet_share_request_schema import PetShareRequestCreate, PetShareApproveRequest


class PetShareRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.share_repo = PetShareRepository(db)
        self.member_repo = FamilyMemberRepository(db)

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
            return error_response(401, "PET_SHARE_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        firebase_uid = decoded.get("uid")

        # 2) User
        user: User = (
            self.db.query(User)
            .select_from(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_SHARE_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 3) Input validation
        effective_search_id = body.pet_search_id if body and body.pet_search_id else pet_search_id
        if not effective_search_id:
            return error_response(400, "PET_SHARE_400_1", "pet_search_id는 필수 값입니다.", path)

        # 4) Pet lookup
        pet = self.share_repo.get_pet_by_search_id(effective_search_id)
        if not pet:
            return error_response(404, "PET_SHARE_404_2", "해당 초대코드에 해당하는 반려동물을 찾을 수 없습니다.", path)

        # 5) Already member?
        if self.share_repo.is_user_in_family(user.user_id, pet.family_id):
            return error_response(409, "PET_SHARE_409_1", "이미 해당 반려동물이 속한 가족 그룹의 구성원입니다.", path)

        # 6) Existing pending?
        if self.share_repo.exists_pending_request(pet.pet_id, user.user_id):
            return error_response(409, "PET_SHARE_409_2", "이미 처리 대기 중인 공유 요청이 존재합니다.", path)

        # 7) Create request
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
            return error_response(500, "PET_SHARE_500_1", "반려동물 공유 요청을 생성하는 중 오류가 발생했습니다.", 
                                  path)

        # 8) Owner lookup (for response; push can be added later)
        owner = self.db.query(User).get(pet.owner_id)

        response_content = {
            "success": True,
            "status": 201,
            "share_request": {
                "id": req.request_id,
                "pet_id": req.pet_id,
                "requester_id": req.requester_id,
                "status": req.status.value if req.status else RequestStatus.PENDING.value,
                "message": req.message,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "responded_at": req.responded_at.isoformat() if req.responded_at else None,
            },
            "pet": {
                "pet_id": pet.pet_id,
                "name": getattr(pet, 'name', None),
                "breed": getattr(pet, 'breed', None),
                "image_url": getattr(pet, 'image_url', None),
            },
            "owner": {
                "user_id": owner.user_id if owner else pet.owner_id,
                "nickname": owner.nickname if owner else None,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }
        return JSONResponse(status_code=201, content=jsonable_encoder(response_content))

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
        if len(parts) != 2:
            return error_response(401, "PET_SHARE_APPROVE_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)
        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "PET_SHARE_APPROVE_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        # 2) User
        firebase_uid = decoded.get("uid")
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_SHARE_APPROVE_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 3) Body validation
        if not body or not body.status:
            return error_response(400, "PET_SHARE_APPROVE_400_1", "status 필드는 필수입니다.", path)
        status_upper = body.status.upper()
        if status_upper not in ("APPROVED", "REJECTED"):
            return error_response(400, "PET_SHARE_APPROVE_400_2", "status는 'APPROVED' 또는 'REJECTED'만 허용됩니다.", path)
        new_status = RequestStatus.APPROVED if status_upper == "APPROVED" else RequestStatus.REJECTED

        # 4) Load request and pet
        req = self.share_repo.get_request_by_id(request_id)
        if not req:
            return error_response(404, "PET_SHARE_APPROVE_404_2", "해당 반려동물 공유 요청을 찾을 수 없습니다.", path)

        pet: Pet = self.db.query(Pet).get(req.pet_id)
        if not pet:
            return error_response(404, "PET_SHARE_APPROVE_404_3", "공유 요청에 연결된 반려동물을 찾을 수 없습니다.", path)

        # 5) Only owner can approve/reject
        if pet.owner_id != user.user_id:
            return error_response(403, "PET_SHARE_APPROVE_403_1", "해당 반려동물의 소유자만 공유 요청을 승인하거나 거절할 수 있습니다.", path)

        # 6) If already processed
        if req.status in (RequestStatus.APPROVED, RequestStatus.REJECTED):
            return error_response(409, "PET_SHARE_APPROVE_409_1", "이미 처리된 공유 요청입니다.", path)

        member_added = False
        created_member = None
        try:
            # Update status
            self.share_repo.update_request_status(req, new_status)

            if new_status == RequestStatus.APPROVED:
                # If requester already member, don't add but keep approved
                if not self.member_repo.is_member(pet.family_id, req.requester_id):
                    try:
                        created_member = self.member_repo.create_member(pet.family_id, req.requester_id)
                        member_added = True
                    except IntegrityError:
                        # Unique constraint may block duplicates → treat as already member
                        self.db.rollback()
                        member_added = False

            self.db.commit()
            self.db.refresh(req)
            if created_member:
                self.db.refresh(created_member)
        except Exception as e:
            print("PET_SHARE_APPROVE_ERROR:", e)
            self.db.rollback()
            return error_response(500, "PET_SHARE_APPROVE_500_1", "반려동물 공유 요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", path)

        # Build response
        resp = {
            "success": True,
            "status": 200,
            "share_request": {
                "id": req.request_id,
                "pet_id": req.pet_id,
                "requester_id": req.requester_id,
                "status": req.status.value,
                "message": req.message,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "responded_at": req.responded_at.isoformat() if req.responded_at else None,
            },
            "member_added": member_added,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }
        if member_added and created_member:
            resp["family_member"] = {
                "id": created_member.member_id,
                "family_id": created_member.family_id,
                "user_id": created_member.user_id,
                "role": created_member.role.value if created_member.role else None,
                "joined_at": created_member.joined_at.isoformat() if created_member.joined_at else None,
            }

        return JSONResponse(status_code=200, content=jsonable_encoder(resp))
