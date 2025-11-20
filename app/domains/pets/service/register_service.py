import re
import json
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from openai import OpenAI

from app.core.config import settings
from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User

# 통합된 repository 구조 기준
from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.pets.repository.family_repository import FamilyRepository

from app.schemas.pets.pet_register_schema import PetRegisterRequest, PetRegisterResponse

class PetRegisterService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)
        self.family_repo = FamilyRepository(db)

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # ============================================================
    # LLM 추천 생성
    # ============================================================
    def _generate_walk_recommendation(self, pet):
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

        Requirements:
        - ALL keys must exist.
        - ALL values must be positive numbers.
        - DO NOT include explanations.
        - DO NOT include backticks.

        Dog info:
        - Name: {pet.name}
        - Age: {pet.age}
        - Weight: {pet.weight}
        - Breed: {pet.breed}
        - Gender: {pet.gender.value if pet.gender else "Unknown"}
        - Disease: {pet.disease if getattr(pet, "disease", None) else "None"}
        """

        try:
            res = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "Output only a valid JSON object. No explanation."},
                    {"role": "user", "content": prompt}
                ],
            )

            content = res.choices[0].message.content.strip()

            # 안전하게 JSON 파싱
            import json
            cleaned = (
                content.replace("```json", "")
                    .replace("```", "")
                    .strip()
            )

            parsed = json.loads(cleaned)

            # 🔥 필수 필드 검사
            required_fields = [
                "min_walks", "min_minutes", "min_distance_km",
                "recommended_walks", "recommended_minutes", "recommended_distance_km",
                "max_walks", "max_minutes", "max_distance_km"
            ]

            missing = [f for f in required_fields if f not in parsed]
            if missing:
                print("누락된 필드:", missing)
                return None

            return parsed

        except Exception as e:
            print("LLM ERROR:", e)
            return None


    # ============================================================
    # 반려동물 등록
    # ============================================================
    def register_pet(self, request: Request, authorization: Optional[str], body: PetRegisterRequest):
        path = request.url.path

        # Auth
        if authorization is None:
            return error_response(401, "PET_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        token = authorization.split(" ")[1]
        decoded = verify_firebase_token(token)
        if decoded is None:
            return error_response(401, "PET_401_2", "유효하지 않거나 만료된 Firebase 토큰입니다.", path)

        firebase_uid = decoded.get("uid")

        # User 조회
        user = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # Body 검증
        if not body.name:
            return error_response(400, "PET_400_1", "반려동물 이름은 필수입니다.", path)

        if body.gender and body.gender not in ("M", "F", "Unknown"):
            return error_response(400, "PET_400_2", "gender 값 오류.", path)

        if not re.fullmatch(r"[A-Za-z0-9]{8}", body.pet_search_id):
            return error_response(400, "PET_400_5", "pet_search_id는 영문+숫자 8자리여야 함.", path)

        if self.pet_repo.exists_pet_search_id(body.pet_search_id):
            return error_response(409, "PET_409_1", "이미 사용 중인 pet_search_id입니다.", path)

        # 트랜잭션
        try:
            # family 생성
            family = self.family_repo.create_family(f"{body.name}네")

            # pet 생성
            pet = self.pet_repo.create_pet(
                family_id=family.family_id,
                owner_id=user.user_id,
                pet_search_id=body.pet_search_id,
                body=body,
            )

            # owner member 등록
            owner_member = self.family_repo.create_owner_member(
                family_id=family.family_id,
                user_id=user.user_id
            )


            # 추천 생성
            rec_data = self._generate_walk_recommendation(pet)
            if rec_data is None:
                raise Exception("RECOMMENDATION_ERROR")

            # rec_data 안에 rec_data 키가 있으면 평탄화
            if "rec_data" in rec_data:
                rec_data = rec_data["rec_data"]

            # 필수 필드가 누락되면 기본값 보정
            defaults = {
                "min_walks": 1,
                "min_minutes": 20,
                "min_distance_km": 1.0,
                "recommended_walks": 2,
                "recommended_minutes": 40,
                "recommended_distance_km": 2.0,
                "max_walks": 3,
                "max_minutes": 60,
                "max_distance_km": 3.0,
            }

            for key, val in defaults.items():
                if key not in rec_data or rec_data[key] is None:
                    rec_data[key] = val

            # 정상 삽입
            recommendation = self.pet_repo.create_recommendation(
                pet_id=pet.pet_id,
                **rec_data,
                generated_by="LLM"
            )


            self.db.commit()

        except Exception as e:
            print("등록 오류:", e)
            self.db.rollback()

            if "RECOMMENDATION_ERROR" in str(e):
                return error_response(500, "PET_500_2", "추천 산책 정보를 생성하는 중 오류.", path)

            return error_response(500, "PET_500_1", "반려동물 등록 중 오류.", path)

        # 성공 응답
        resp = {
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
                "disease": pet.disease,
                "image_url": pet.image_url,
                "created_at": pet.created_at.isoformat() if pet.created_at else None,
                "updated_at": pet.updated_at.isoformat() if pet.updated_at else None,

            },
            "family": {
                "id": family.family_id,
                "family_name": family.family_name,
                "created_at": family.created_at,
                "updated_at": family.updated_at,
            },
            "owner_member": {
                "id": owner_member.member_id,
                "family_id": owner_member.family_id,
                "user_id": owner_member.user_id,
                "role": owner_member.role.value,
                "joined_at": owner_member.joined_at,
            },
            "recommendation": {
                "rec_id": recommendation.rec_id,
                "pet_id": recommendation.pet_id,
                "min_walks": recommendation.min_walks,
                "min_minutes": recommendation.min_minutes,
                "min_distance_km": recommendation.min_distance_km,
                "recommended_walks": recommendation.recommended_walks,
                "recommended_minutes": recommendation.recommended_minutes,
                "recommended_distance_km": recommendation.recommended_distance_km,
                "max_walks": recommendation.max_walks,
                "max_minutes": recommendation.max_minutes,
                "max_distance_km": recommendation.max_distance_km,
                "generated_by": recommendation.generated_by,
                "updated_at": recommendation.updated_at,
            },
            "timeStamp": datetime.utcnow(),
            "path": path,
        }

        return PetRegisterResponse(**resp)
