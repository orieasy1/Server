import re
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User

from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.pets.repository.family_repository import FamilyRepository
from app.domains.pets.repository.family_member_repository import FamilyMemberRepository
from app.domains.pets.repository.pet_recommendation_repository import PetRecommendationRepository

from app.schemas.pets.pet_register_schema import PetRegisterRequest


class PetRegisterService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.family_repo = FamilyRepository(db)
        self.member_repo = FamilyMemberRepository(db)
        self.rec_repo = PetRecommendationRepository(db)

    def register_pet(
        self,
        request: Request,
        authorization: Optional[str],
        body: PetRegisterRequest,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return error_response(401, "PET_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(
                401, "PET_401_2",
                "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.",
                path
            )

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(
                401, "PET_401_3",
                "Authorization 헤더 형식이 잘못되었습니다.",
                path
            )

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return error_response(
                401, "PET_401_2",
                "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.",
                path
            )

        firebase_uid = decoded.get("uid")

        # ============================================
        # 2) 사용자 조회
        # ============================================
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            return error_response(
                404, "PET_404_1",
                "해당 사용자를 찾을 수 없습니다.",
                path
            )

        # ============================================
        # 3) Body 검증
        # ============================================
        if not body.name:
            return error_response(400, "PET_400_1", "반려동물 이름(name)은 필수입니다.", path)

        if body.gender and body.gender not in ["M", "F", "Unknown"]:
            return error_response(
                400, "PET_400_2",
                "gender는 'M', 'F', 'Unknown' 중 하나여야 합니다.",
                path
            )

        # pet_search_id 필수
        if not body.pet_search_id:
            return error_response(
                400, "PET_400_4",
                "pet_search_id는 필수입니다.",
                path
            )

        # 형식: 영문 + 숫자 8자리
        if not re.fullmatch(r"[A-Za-z0-9]{8}", body.pet_search_id):
            return error_response(
                400, "PET_400_5",
                "pet_search_id는 영문 대소문자와 숫자로 이루어진 8자리여야 합니다.",
                path
            )

        # 중복 체크
        if self.pet_repo.exists_pet_search_id(body.pet_search_id):
            return error_response(
                409, "PET_409_1",
                "이미 사용 중인 pet_search_id입니다.",
                path
            )

        # ============================================
        # 4) 트랜잭션 시작 (family → pet → member → rec)
        # ============================================
        try:
            # family 생성
            family_name = f"{body.name}네" if body.name else "우리집"
            family = self.family_repo.create_family(family_name)

            # pet 생성
            pet = self.pet_repo.create_pet(
                family_id=family.family_id,
                owner_id=user.user_id,
                pet_search_id=body.pet_search_id,
                body=body,
            )

            # family member 등록
            member = self.member_repo.create_owner_member(
                family_id=family.family_id,
                user_id=user.user_id,
            )

            # 추천 산책 정보 생성 (임시 값)
            recommendation = self.rec_repo.create_recommendation(
                pet_id=pet.pet_id,
                min_walks=1,
                min_minutes=20,
                min_distance_km=1.0,
                recommended_walks=2,
                recommended_minutes=40,
                recommended_distance_km=2.0,
                max_walks=3,
                max_minutes=60,
                max_distance_km=3.0,
                generated_by="LLM",
            )

            self.db.commit()

        except Exception as e:
            print("PET_REGISTER_ERROR:", e)
            self.db.rollback()
            return error_response(
                500, "PET_500_1",
                "반려동물을 등록하는 중 오류가 발생했습니다.",
                path
            )

        # ============================================
        # 5) 성공 응답
        # ============================================
        response_content = {
            "success": True,
            "status": 201,
            "pet": {
                "pet_id": pet.pet_id,
                "family_id": pet.family_id,
                "owner_id": pet.owner_id,
                "pet_search_id": pet.pet_search_id,
                "name": pet.name,
                "breed": pet.breed,
                "age": pet.age,
                "weight": pet.weight,
                "gender": pet.gender.value if pet.gender else None,
                "image_url": pet.image_url,
                "created_at": pet.created_at.isoformat() if pet.created_at else None,
                "updated_at": pet.updated_at.isoformat() if pet.updated_at else None,
            },
            "family": {
                "id": family.family_id,
                "family_name": family.family_name,
                "created_at": family.created_at.isoformat() if family.created_at else None,
                "updated_at": family.updated_at.isoformat() if family.updated_at else None,
            },
            "owner_member": {
                "id": member.member_id,
                "family_id": member.family_id,
                "user_id": member.user_id,
                "role": member.role.value if member.role else None,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            },
            "recommendation": {
                "rec_id": recommendation.rec_id,
                "pet_id": recommendation.pet_id,
                "min_walks": recommendation.min_walks,
                "min_minutes": recommendation.min_minutes,
                "min_distance_km": float(recommendation.min_distance_km),
                "recommended_walks": recommendation.recommended_walks,
                "recommended_minutes": recommendation.recommended_minutes,
                "recommended_distance_km": float(recommendation.recommended_distance_km),
                "max_walks": recommendation.max_walks,
                "max_minutes": recommendation.max_minutes,
                "max_distance_km": float(recommendation.max_distance_km),
                "generated_by": recommendation.generated_by,
                "updated_at": recommendation.updated_at.isoformat() if recommendation.updated_at else None,
            },
            "timeStamp": family.created_at.isoformat() if family.created_at else None,
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=201, content=encoded)

