from sqlalchemy.orm import Session
from typing import Optional

from app.models.family import Family
from app.models.family_member import FamilyMember, MemberRole


class FamilyRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------
    # Family
    # -------------------------------
    def create_family(self, family_name: str) -> Family:
        family = Family(family_name=family_name)
        self.db.add(family)
        self.db.flush()
        return family

    def get_by_id(self, family_id: int) -> Optional[Family]:
        return self.db.get(Family, family_id)

    # -------------------------------
    # Members
    # -------------------------------
    def create_owner_member(self, family_id: int, user_id: int):
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            role=MemberRole.OWNER,
        )
        self.db.add(member)
        self.db.flush()
        return member

    def create_member(self, family_id: int, user_id: int):
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            role=MemberRole.MEMBER,
        )
        self.db.add(member)
        self.db.flush()
        return member

    def is_member(self, family_id: int, user_id: int) -> bool:
        return (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id,
            )
            .first()
            is not None
        )
