import json
from datetime import datetime
from typing import Optional

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response

from app.models.user import User
from app.models.pet import Pet, PetGender
from app.models.family_member import FamilyMember, MemberRole

from app.domains.pets.repository.pet_repository import PetRepository
from app.schemas.pets.pet_update_schema import PetUpdateRequest


class PetModifyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PetRepository(db)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # --------------------------------------------------
    # 🔥 LLM 추천 산책 정보 생성 (수정 시 호출)
    # --------------------------------------------------
    def _generate_recommendation(self, pet: Pet):
        prompt = f"""
        You must output ONLY a valid JSON object.
        Use exactly these keys, all required:

        {{
            "min_walks": int,
            "min_minutes": int,
            "min_distance_km": float,
            "recommended_walks": int,
            "recommended_minutes": int,
            "recommended_distance_km": float,
            "max_walks": int,
            "max_minutes": int,
            "max_distance_km": float
        }}

        Dog info:
        - Name: {pet.name}
        - Age: {pet.age}
        - Weight: {pet.weight}
        - Breed: {pet.breed}
        - Gender: {pet.gender.value if pet.gender else "Unknown"}
        - Disease: {pet.disease if getattr(pet, "disease", None) else "None"}

        Rules:
        - MUST output only JSON, no text.
        - All fields must exist.
        - All numbers must be positive.
        """

        try:
            res = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "Output only a valid JSON object. No explanation."},
                    {"role": "user", "content": prompt},
                ],
            )

            content = res.choices[0].message.content.strip()
            cleaned = content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned)

            required = [
                "min_walks", "min_minutes", "min_distance_km",
                "recommended_walks", "recommended_minutes", "recommended_distance_km",
                "max_walks", "max_minutes", "max_distance_km"
            ]

            missing = [f for f in required if f not in parsed]
            if missing:
                print("누락된 필드:", missing)
                return None

            return parsed

        except Exception as e:
            print("LLM ERROR:", e)
            return None

    # --------------------------------------------------
    # 🔥 반려동물 정보 수정
    # --------------------------------------------------
    def update_pet_detail(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: int,
        body: PetUpdateRequest,
    ):
        path = request.url.path

        # ========== Auth ==========
        if authorization is None:
            return error_response(401, "PET_EDIT_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_EDIT_401_2", "Authorization 형식 오류", path)

        decoded = verify_firebase_token(authorization.split(" ")[1])
        if decoded is None:
            return error_response(401, "PET_EDIT_401_2", "Firebase 토큰 검증 실패", path)

        # user 조회
        user = (
            self.db.query(User)
            .filter(User.firebase_uid == decoded["uid"])
            .first()
        )
        if not user:
            return error_response(404, "PET_EDIT_404_1", "사용자를 찾을 수 없습니다.", path)

        # pet 조회
        pet = self.repo.get_by_id(pet_id)
        if not pet:
            return error_response(404, "PET_EDIT_404_2", "반려동물을 찾을 수 없습니다.", path)

        # 권한 체크: owner or owner_member
        if not (pet.owner_id == user.user_id or self._is_owner_member(user.user_id, pet)):
            return error_response(403, "PET_EDIT_403_1", "수정 권한이 없습니다.", path)

        # body empty validation (🚩 disease 포함)
        if not body or all(
            getattr(body, f) is None
            for f in ["name", "breed", "age", "weight", "gender", "disease"]
        ):
            return error_response(400, "PET_EDIT_400_1", "수정할 항목이 없습니다.", path)

        # gender enum 변환
        gender_enum = None
        if body.gender == "M":
            gender_enum = PetGender.M
        elif body.gender == "F":
            gender_enum = PetGender.F
        elif body.gender == "Unknown":
            gender_enum = PetGender.Unknown

        # ========== UPDATE ==========
        try:
            updated_pet = self.repo.update_partial(
                pet,
                name=body.name,
                breed=body.breed,
                age=body.age,
                weight=body.weight,
                gender=gender_enum,
                disease=body.disease,   # ✅ disease 반영
            )
        except Exception as e:
            print("PARTIAL UPDATE ERROR:", e)
            self.db.rollback()
            return error_response(500, "PET_EDIT_500_1", "반려동물 정보를 수정하는 중 오류.", path)

        # ========== LLM Recommendation regenerate ==========
        # disease도 추천에 영향을 줄 수 있으니 여기에도 포함해줄게
        need_llm = any(
            getattr(body, f) is not None
            for f in ["breed", "age", "weight", "gender", "disease"]
        )

        rec_dict = None

        if need_llm:
            rec_json = self._generate_recommendation(updated_pet)
            if rec_json is None:
                return error_response(500, "PET_EDIT_500_2", "추천 산책 정보 생성 실패", path)

            rec_obj = self.repo.get_recommendation(pet_id)
            if rec_obj:
                rec_obj = self.repo.update_recommendation(rec_obj, **rec_json)
            else:
                rec_obj = self.repo.create_recommendation(pet_id, **rec_json)

            rec_dict = {**rec_json, "rec_id": rec_obj.rec_id}

        self.db.commit()
        self.db.refresh(updated_pet)

        # ========== Response ==========
        resp = {
            "success": True,
            "status": 200,
            "pet": {
                "pet_id": updated_pet.pet_id,
                "family_id": updated_pet.family_id,
                "owner_id": updated_pet.owner_id,
                "pet_search_id": updated_pet.pet_search_id,
                "name": updated_pet.name,
                "breed": updated_pet.breed,
                "age": updated_pet.age,
                "weight": updated_pet.weight,
                "gender": updated_pet.gender.value if updated_pet.gender else None,
                "disease": updated_pet.disease,   # ✅ 응답에도 포함
                "image_url": updated_pet.image_url,
                "created_at": updated_pet.created_at.isoformat(),
                "updated_at": updated_pet.updated_at.isoformat(),
            },
            "recommendation": rec_dict,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }

        return JSONResponse(status_code=200, content=jsonable_encoder(resp))

    # --------------------------------------------------
    # OWNER 체크
    # --------------------------------------------------
    def _is_owner_member(self, user_id: int, pet: Pet) -> bool:
        fm = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.role == MemberRole.OWNER,
            )
            .first()
        )
        return fm is not None

    # --------------------------------------------------
    # 🔥 반려동물 이미지 수정
    # --------------------------------------------------
    def update_pet_image(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: int,
        image_url: str,
    ):
        path = request.url.path

        # Auth
        if authorization is None:
            return error_response(401, "PET_IMG_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_IMG_401_2", "Authorization 형식 오류", path)

        decoded = verify_firebase_token(authorization.split(" ")[1])
        if decoded is None:
            return error_response(401, "PET_IMG_401_2", "Firebase 토큰 검증 실패", path)

        # user
        user = (
            self.db.query(User)
            .filter(User.firebase_uid == decoded["uid"])
            .first()
        )
        if not user:
            return error_response(404, "PET_IMG_404_1", "사용자를 찾을 수 없습니다.", path)

        # pet
        pet = self.repo.get_by_id(pet_id)
        if not pet:
            return error_response(404, "PET_IMG_404_2", "반려동물을 찾을 수 없습니다.", path)

        # owner check
        if not (pet.owner_id == user.user_id or self._is_owner_member(user.user_id, pet)):
            return error_response(403, "PET_IMG_403_1", "이미지 수정 권한이 없습니다.", path)

        try:
            pet.image_url = image_url
            self.db.commit()
            self.db.refresh(pet)
        except Exception:
            self.db.rollback()
            return error_response(500, "PET_IMG_500_2", "이미지 URL 저장 중 오류.", path)

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    "success": True,
                    "status": 200,
                    "image_url": image_url,
                    "timeStamp": datetime.utcnow().isoformat(),
                    "path": path,
                }
            ),
        )
