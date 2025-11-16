from sqlalchemy.orm import Session
from app.models.pet_walk_recommendation import PetWalkRecommendation
from typing import Optional


class PetRecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendation_by_pet_id(self, pet_id: int):
        return (
            self.db.query(PetWalkRecommendation)
            .filter(PetWalkRecommendation.pet_id == pet_id)
            .first()
        )

    def create_recommendation(
        self,
        pet_id: int,
        min_walks: int,
        min_minutes: int,
        min_distance_km: float,
        recommended_walks: int,
        recommended_minutes: int,
        recommended_distance_km: float,
        max_walks: int,
        max_minutes: int,
        max_distance_km: float,
        generated_by: str = "LLM",
    ) -> PetWalkRecommendation:
        rec = PetWalkRecommendation(
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
            generated_by=generated_by,
        )
        self.add_rec(rec)
        return rec

    def add_rec(self, rec: PetWalkRecommendation):
        self.add(rec)

    def add(self, entity):
        self.db.add(entity)
        self.db.flush()

    def update_recommendation(
        self,
        rec: PetWalkRecommendation,
        *,
        min_walks: int,
        min_minutes: int,
        min_distance_km: float,
        recommended_walks: int,
        recommended_minutes: int,
        recommended_distance_km: float,
        max_walks: int,
        max_minutes: int,
        max_distance_km: float,
        generated_by: Optional[str] = None,
    ) -> PetWalkRecommendation:
        rec.min_walks = min_walks
        rec.min_minutes = min_minutes
        rec.min_distance_km = min_distance_km
        rec.recommended_walks = recommended_walks
        rec.recommended_minutes = recommended_minutes
        rec.recommended_distance_km = recommended_distance_km
        rec.max_walks = max_walks
        rec.max_minutes = max_minutes
        rec.max_distance_km = max_distance_km
        if generated_by:
            rec.saved_generated_by = None
            rec.generated_by = generated_by
        self.db.flush()
        return rec
