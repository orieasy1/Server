from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.family_member import FamilyMember, MemberRole


class FamilyMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_owner_member(self, family_id: int, user_id: int) -> FamilyMember:
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            role=MemberRole.OWNER,
        )
        self.db.add(member)
        self.db.flush()
        return member

    def is_member(self, family_id: int, user_id: int) -> bool:
        return (
            self.db.query(FamilyMember)
            .filter(and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == user_id
            ))
            .first()
            is not None
        )

    def create_member(self, family_id: int, user_id: int) -> FamilyMember:
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            role=MemberRole.MEMBER,
        )
        self.db.add(member)
        self.db.flush()
        return member
