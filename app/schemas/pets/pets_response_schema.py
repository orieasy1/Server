from pydantic import BaseModel
from datetime import datetime
from app.models.pet import PetGender

class PetResponse(BaseModel):
    pet_id: int
    family_id: int
    owner_id: int
    pet_search_id: str
    name: str
    breed: str | None
    age: int | None
    weight: float | None
    gender: PetGender
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # ORM 모델 자동 변환
