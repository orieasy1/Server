from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token
from app.domains.walk.exception import walk_error
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.domains.walk.repository.recommendation_repository import RecommendationRepository


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.recommendation_repo = RecommendationRepository(db)

    def get_recommendation(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: int,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return walk_error("WALK_REC_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_REC_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return walk_error("WALK_REC_401_2", path)

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return walk_error("WALK_REC_401_2", path)

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
            return walk_error("WALK_REC_404_1", path)

        # ============================================
        # 3) 반려동물 조회
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == pet_id)
            .first()
        )

        if not pet:
            return walk_error("WALK_REC_404_2", path)

        # ============================================
        # 4) 권한 체크 (family_members 확인)
        # ============================================
        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return walk_error("WALK_REC_403_1", path)

        # ============================================
        # 5) 추천 산책 정보 조회
        # ============================================
        try:
            recommendation = self.recommendation_repo.get_recommendation_by_pet_id(pet_id)

            if not recommendation:
                return walk_error("WALK_REC_404_3", path)

        except Exception as e:
            print("RECOMMENDATION_QUERY_ERROR:", e)
            return walk_error("WALK_REC_500_1", path)

        # ============================================
        # 6) 응답 생성
        # ============================================
        # per_walk 계산 (추천 산책 횟수로 나눔)
        recommended_minutes_per_walk = (
            recommendation.recommended_minutes // recommendation.recommended_walks
            if recommendation.recommended_walks > 0 else 0
        )
        recommended_distance_km_per_walk = (
            float(recommendation.recommended_distance_km) / recommendation.recommended_walks
            if recommendation.recommended_walks > 0 else 0.0
        )

        response_content = {
            "success": True,
            "status": 200,
            "recommendation": {
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
                "per_walk": {
                    "recommended_minutes_per_walk": recommended_minutes_per_walk,
                    "recommended_distance_km_per_walk": round(recommended_distance_km_per_walk, 2)
                }
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)


