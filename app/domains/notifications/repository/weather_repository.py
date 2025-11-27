# app/domains/notifications/repository/weather_repository.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.models.pet_walk_recommendation import PetWalkRecommendation
from app.models.walk import Walk


class WeatherRepository:
    def __init__(self, db: Session):
        self.db = db

    # -----------------------
    # PET 조회
    # -----------------------
    def get_pet(self, pet_id: int):
        return (
            self.db.query(Pet)
            .filter(Pet.pet_id == pet_id)
            .first()
        )

    # -----------------------
    # user가 pet family에 속하는지 체크
    # -----------------------
    def user_in_family(self, user_id: int, family_id: int) -> bool:
        return (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.user_id == user_id,
                FamilyMember.family_id == family_id
            )
            .first()
            is not None
        )

    # -----------------------
    # 최근 7일 산책 시간(분) 총합
    # -----------------------
    def get_weekly_walk_minutes(self, pet_id: int) -> int:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        total = (
            self.db.query(func.sum(Walk.duration_min))
            .filter(
                Walk.pet_id == pet_id,
                Walk.start_time >= seven_days_ago
            )
            .scalar()
        )

        return int(total or 0)

    # -----------------------
    # 추천 산책 정보 조회
    # -----------------------
    def get_recommendation(self, pet_id: int):
        return (
            self.db.query(PetWalkRecommendation)
            .filter(PetWalkRecommendation.pet_id == pet_id)
            .first()
        )

    # -----------------------
    # 최근 산책 1건 조회
    # -----------------------
    def get_last_walk_record(self, pet_id: int):
        return (
            self.db.query(Walk)
            .filter(Walk.pet_id == pet_id)
            .order_by(Walk.end_time.desc().nullslast())  # ⭐ 개선 포인트
            .first()
        )
