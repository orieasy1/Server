from sqlalchemy.orm import Session
from app.models.family_member import FamilyMember


class FamilyMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_owner_member(self, family_id: int, user_id: int) -> FamilyMember:
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            role="OWNER",
        )
        self.db.add(member)
        self.db.flush()
        return member
