from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.models.pet import Pet, PetGender
from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.pets.repository.pet_recommendation_repository import PetRecommendationRepository
from app.models.family_member import FamilyMember, MemberRole
from app.schemas.pets.pet_update_schema import PetUpdateRequest


class PetUpdateService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.rec_repo = PetRecommendationRepository(db)

    def patch_pet(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: int,
        body: PetUpdateRequest,
    ):
        path = request.url.path

        # Auth
        if authorization is None:
            return error_response(401, "PET_EDIT_401_1", "Authorization 헤더가 필요합니다.", path)
        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_EDIT_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)
        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "PET_EDIT_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)
        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "PET_EDIT_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        # User
        firebase_uid = decoded.get("uid")
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_EDIT_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # Pet
        pet: Optional[Pet] = self.pet_repo.get_by_id(pet_id)
        if not pet:
            return error_response(404, "PET_EDIT_404_2", "요청하신 반려동물을 찾을 수 없습니다.", path)

        # Owner check
        if not (pet.owner_id == user.user_id or self._is_owner_member(user.user_id, pet)):
            return error_response(403, "PET_EDIT_403_1", "해당 반려동물 정보를 수정할 권한이 없습니다.", path)

        # Validate body
        if not body or all(
            getattr(body, f) is None for f in ["name", "breed", "age", "weight", "gender"]
        ):
            return error_response(400, "PET_EDIT_400_1", "수정할 필드가 존재하지 않습니다.", path)

        if body.gender is not None:
            if body.gender not in ("M", "F", "Unknown"):
                return error_response(400, "PET_EDIT_400_2", "gender는 'M', 'F', 'Unknown' 중 하나여야 합니다.", path)

        if body.age is not None and (not isinstance(body.age, int) or body.age < 0):
            return error_response(400, "PET_EDIT_400_3", "나이 또는 몸무게 형식이 올바르지 않습니다.", path)
        if body.changes_weight := (body.weight is not None):
            try:
                _ = float(body.weight)
                if body.weight is not None and body.weight <= 0:
                    return error_response(400, "PET_EDIT_400_3", "나이 또는 몸무게 형식이 올바르지 않습니다.", path)
            except Exception:
                return error_response(400, "PET_EDIT_400_3", "나이 또는 몸무게 형식이 올바르지 않습니다.", path)

        # Apply partial update
        try:
            new_pet = self.pet_repo.update_partial(
                pet,
                name=body.name,
                breed=body.breed,
                age=body.age,
                weight=body.weight,
                gender=self._to_gender_enum(body.gender) if body.gender is not None else None,
            )
        except Exception as e:
            print("PET_UPDATE_ERROR:", e)
            self.db.rollback()
            return error_response(500, "PET_EDIT_500_1", "반려동물 정보를 수정하는 중 오류가 발생했습니다.", path)

        # Recompute recommendation if non-name attributes changed
        rec_payload_changed = any(
            getattr(body, f) is not None for f in ["breed", "age", "weight", "gender"]
        )
        rec_dict = None
        if rec_payload_changed:
            try:
                rec = self.rec_repo.get_recommendation_by_pet_id(pet_id)
                # naive heuristic for demo purposes; replace with real LLM call later
                min_walks = 1
                min_minutes = 20 if (body.age or (new_pet.age or 0)) < 5 else 30
                min_distance_km = 1.0
                recommended_walks = 2
                recommended_minutes = 40 if (new_pet.weight or 0) < 5 else 45
                recommended_distance_km = 2.0 if (new_pet.weight or 0) < 5 else 2.2
                max_walks = 3
                max_minutes = 60 if (new_pet.weight or 0) < 5 else 70
                max_distance_km = 3.0 if (new_pet.weight or 0) < 5 else 3.5

                if rec:
                    rec = self.rec_repo.update_recommendation(
                        rec,
                        min_walks=min_walks,
                        min_minutes=min_minutes,
                        min_distance_km=min_distance_km,
                        recommended_walks=recommended_walks,
                        recommended_minutes=recommended_minutes,
                        recommended_distance_km=recommended_distance_km,
                        max_walks=max_walks,
                        max_minutes=max_minutes,
                        max_distance_km=max_distance_km,
                        generated_by="LLM",
                    )
                else:
                    rec = self.rec_repo.create_recommendation(
                        pet_id=pet_id,
                        min_walks=min_walks,
                        min_minutes=min_minutes,
                        min_distance_km=min_distance_km,
                        recommended_walks=recommended_walks,
                        recommended_minutes=recommended_minutes,
                        recommended_distance_km=recommended_distance_km,
                        max_walks=max_walks,
                        max_minutes=max_minutes,
                        max_distance_km=max_distance_km,
                        generated_by="LLM",
                    )
                self.db.commit()
                self.db.refresh(new_pet)
                self.db.refresh(rec)
                rec_dict = {
                    "rec_id": rec.__dict__.get("rec_id"),
                    "pet_id": rec.pet_id,
                    "min_walks": rec.min_walks,
                    "min_minutes": rec.min_minutes,
                    "min_distance_km": float(rec.min_distance_km),
                    "recommended_walks": rec.recommended_walks,
                    "recommended_minutes": rec.recommended_minutes,
                    "recommended_distance_km": float(rec.recommended_distance_km),
                    "max_walks": rec.max_walks,
                    "max_minutes": rec.max_minutes,
                    "max_distance_km": float(rec.max_distance_km),
                    "generated_by": rec.generated_by,
                    "updated_at": rec.updated_at.isoformat() if hasattr(rec, 'updated_at') and rec.updated_at else None,
                }
            except Exception as e:
                print("PET_RECOMMEND_RECOMPUTE_ERROR:", e)
                self.db.rollback()
                return error_response(500, "PET_EDIT_500_2", "추천 산책 정보를 다시 계산하는 중 오류가 발생했습니다.", path)
        else:
            # still commit name-only change
            try:
                self.db.commit()
                self.db.refresh(new_pet)
            except Exception as e:
                print("PET_UPDATE_COMMIT_ERROR:", e)
                self.db.rollback()
                return error_response(500, "PET_EDIT_500_1", "곤약", path)

        resp = {
            "success": True,
            "status": 200,
            "pet": {
                "pet_id": new_pet.pet_id,
                "family_id": new_pet.family_id,
                "owner_id": new_pet.owner_id,
                "pet_search_id": new_pet.pet_search_id,
                "name": new_pet.name,
                "breed": getattr(new_pet, 'breed', None),
                "age": getattr(new_pet, 'age', None),
                "weight": getattr(new_pet, 'weight', None),
                "gender": new_pet.gender.value if hasattr(new_pet, 'gender') and new_pet.gender else None,
                "image_url": getattr(new_pet, 'image_url', None),
                "created_at": new_pet.created_at.isoformat() if new_pet.created_at else None,
                "updated_at": new_pet.updated_at.isoformat() if hasattr(new_pet, 'updated_at') and new_pet.updated_at else None,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }
        if rec_dict:
            resp["recommendation"] = rec_dict
        return JSONResponse(status_code=200, content=jsonable_encoder(resp))

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

    def _to_gender_enum(self, val: Optional[str]):
        if val is None:
            return None
        if val == "M":
            return PetGender.M
        if val == "F":
            return PetGender.F
        return PetGender.Unknown
