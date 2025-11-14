from sqlalchemy.orm import Session
from app.models.pet_walk_recommendation import PetWalkRecommendation


class PetRecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

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

        self.db.add(rec)
        self.db.flush()
        return rec
