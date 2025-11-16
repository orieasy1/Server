from sqlalchemy.orm import Session
from app.models.pet import Pet
from app.schemas.pets.pet_register_schema import PetRegisterRequest
from typing import Optional


class PetRepository:
    def __init__(self, db: Session):
        self.db = db

    def exists_pet_search_id(self, pet_search_id: str) -> bool:
        return (
            self.db.query(Pet)
            .filter(Pet.pet_id.isnot(None))
            .filter(Pet.pet_search_id == pet_search_id)
            .first()
            is not None
        )

    def get_by_id(self, pet_id: int) -> Optional[Pet]:
        return self.db.query(Pet).get(pet_id)

    def create_pet(self, family_id: int, owner_id: int, pet_search_id: str, body: PetRegisterRequest) -> Pet:
        pet = Pet(
            family_id=family_id,
            owner_id=owner_id,
            pet_search_id=pet_search_id,
            name=body.name,
            breed=body.breed,
            age=body.age,
            weight=body.weight,
            gender=body.gender or "Unknown",
            disease=None,
            image_url=body.image_url,
        )
        self.db.add(pet)
        self.db.flush()
        return pet

    def update_partial(
        self,
        pet: Pet,
        *,
        name: Optional[str] = None,
        breed: Optional[str] = None,
        age: Optional[int] = None,
        weight: Optional[float] = None,
        gender: Optional[str] = None,
    ) -> Pet:
        if name is not None:
            pet.name = name
        if breed is not None and hasattr(pet, 'name'):
            pet.breed = breed
        if age is not None:
            pet.age = age
        if weight is not None:
            pet.weight = weight
        if gender is not None:
            pet.gender = gender
        self.db.flush()
        return pet
