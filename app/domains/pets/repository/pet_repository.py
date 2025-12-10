from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List

from app.models.pet import Pet, PetGender
from app.models.pet_walk_recommendation import PetWalkRecommendation
from app.models.family import Family
from app.models.family_member import FamilyMember, MemberRole


class PetRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------
    # PET: CRUD
    # -------------------------------
    def get_by_id(self, pet_id: int) -> Optional[Pet]:
        return self.db.get(Pet, pet_id)

    def get_by_search_id(self, pet_search_id: str) -> Optional[Pet]:
        return (
            self.db.query(Pet)
            .filter(Pet.pet_search_id == pet_search_id)
            .first()
        )

    def exists_pet_search_id(self, pet_search_id: str) -> bool:
        return (
            self.db.query(Pet)
            .filter(Pet.pet_search_id == pet_search_id)
            .first()
            is not None
        )

    def create_pet(self, family_id: int, owner_id: int, pet_search_id: str, body):
        # 🔥 gender 문자열을 Enum으로 변환
        gender = body.gender
        if isinstance(gender, str):
            try:
                gender = PetGender(gender)   # "M" / "F" / "Unknown" → Enum
            except ValueError:
                # 잘못된 값 들어오면 그냥 None 처리 (혹은 raise 해도 됨)
                gender = None

        pet = Pet(
            family_id=family_id,
            owner_id=owner_id,
            pet_search_id=pet_search_id,
            name=body.name,
            breed=body.breed,
            age=body.age,
            weight=body.weight,
            gender=gender,                 # 🔥 여기 Enum(or None) 들어감
            disease=body.disease,
            image_url=body.image_url,
            voice_url=getattr(body, 'voice_url', None),  # 음성 녹음 URL
        )
        self.db.add(pet)
        self.db.flush()  # pet.pet_id 사용 가능
        return pet


    def update_partial(self, pet: Pet, **kwargs) -> Pet:
        for k, v in kwargs.items():
            if v is not None:
                setattr(pet, k, v)
        self.db.flush()
        return pet

    # -------------------------------
    # MY PETS 목록 조회
    # -------------------------------
    def get_pets_for_user(self, user_id: int):
        return (
            self.db.query(Pet, Family)
            .join(Family, Family.family_id == Pet.family_id)
            .join(FamilyMember, FamilyMember.family_id == Pet.family_id)
            .filter(FamilyMember.user_id == user_id)
            .order_by(
                (Pet.owner_id == user_id).desc(),  # 내가 owner인 pet 먼저
                Pet.created_at.desc(),              # 그 다음 최신순
            )
            .all()
        )

    # -------------------------------
    # RECOMMENDATION
    # -------------------------------

    def get_recommendation(self, pet_id: int) -> Optional[PetWalkRecommendation]:
        return (
            self.db.query(PetWalkRecommendation)
            .filter(PetWalkRecommendation.pet_id == pet_id)
            .first()
        )

    def create_recommendation(self, pet_id: int, **kwargs) -> PetWalkRecommendation:
        rec = PetWalkRecommendation(pet_id=pet_id, **kwargs)
        self.db.add(rec)
        self.db.flush()
        return rec

    def update_recommendation(self, rec: PetWalkRecommendation, **kwargs):
        for k, v in kwargs.items():
            setattr(rec, k, v)
        self.db.flush()
        return rec
