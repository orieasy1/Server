from sqlalchemy.orm import Session
from sqlalchemy import and_, case
from typing import List

from app.models.pet import Pet
from app.models.family import Family
from app.models.family_member import FamilyMember


class MyPetsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_pets_for_user(self, user_id: int) -> List[tuple]:
        """
        Return list of tuples (Pet, Family, is_owner: bool), ordered by owner-first then newest pet.
        """
        # families where user is a member
        subq = self.db.query(FamilyMember.family_id).filter(FamilyMember.user_id == user_id).subquery()

        is_owner_order = case((Pet.owner_id == user_id, 0), else_=1)
        q = (
            self.db.query(Pet, Family, is_owner_order.label("owner_rank"))
            .join(Family, Family.family_id == Pet.family_id)
            .filter(Pet.family_id.in_(subq))
            .order_by(is_owner_order.asc(), Pet.created_at.desc())
        )
        rows = q.all()
        # Convert to (Pet, Family, bool)
        return [(p, f, True if rank == 0 else False) for (p, f, rank) in rows]
