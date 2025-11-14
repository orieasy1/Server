from sqlalchemy.orm import Session
from app.models.pet import Pet
from app.schemas.pets.pet_register_schema import PetRegisterRequest


class PetRepository:
    def __init__(self, db: Session):
        self.db = db

    def exists_pet_search_id(self, pet_search_id: str) -> bool:
        return (
            self.db.query(Pet)
            .filter(Pet.pet_search_id == pet_search_id)
            .first()
            is not None
        )

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
