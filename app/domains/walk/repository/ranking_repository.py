# app/domains/walk/repository/ranking_repository.py

from sqlalchemy.orm import Session
from sqlalchemy import func, desc   \

from app.models.walk import Walk
from app.models.family_member import FamilyMember
from app.models.pet import Pet


class RankingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_family_members(self, family_id: int):
        return (
            self.db.query(FamilyMember.user_id)
            .filter(FamilyMember.family_id == family_id)
            .all()
        )

    def check_family_exists(self, family_id: int):
        return (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id)
            .first()
        )

    def get_walk_stats(self, user_ids, start_dt, end_dt, pet_id=None):
        """
        각 user_id 별로 이번 기간 동안의
        - 총 거리(km)
        - 총 시간(min)
        - 산책 횟수
        를 집계하고, 아래 기준으로 정렬한다:

        ORDER BY total_distance_km DESC,
                 total_duration_min DESC,
                 walk_count DESC
        """
        if not user_ids:
            return []

        query = (
            self.db.query(
                Walk.user_id,
                func.coalesce(func.sum(Walk.distance_km), 0).label("total_distance_km"),
                func.coalesce(func.sum(Walk.duration_min), 0).label("total_duration_min"),  # ✅ 컬럼명 수정
                func.count(Walk.walk_id).label("walk_count"),
            )
            .filter(Walk.user_id.in_(user_ids))
            .filter(Walk.start_time >= start_dt)
            .filter(Walk.start_time < end_dt)  
        )

        if pet_id is not None:
            query = query.filter(Walk.pet_id == pet_id)

        query = (
            query.group_by(Walk.user_id)
            .order_by(
                desc("total_distance_km"),  
                desc("total_duration_min"),
                desc("walk_count"),
            )
        )

        return query.all()

    def get_user_pets(self, user_id, start_dt, end_dt):
        """유저가 이번 기간 동안 산책한 pet 목록"""
        return (
            self.db.query(
                Pet.pet_id,
                Pet.name,
                Pet.image_url,
            )
            .join(Walk, Walk.pet_id == Pet.pet_id)
            .filter(Walk.user_id == user_id)
            .filter(Walk.start_time >= start_dt)
            .filter(Walk.start_time < end_dt) 
            .group_by(Pet.pet_id, Pet.name, Pet.image_url) 
            .all()
        )
