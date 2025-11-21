from sqlalchemy.orm import Session
from app.models.user import User
from app.models.family_member import FamilyMember
from typing import List, Optional


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

    # 🔥 유저가 속한 모든 가족 row 조회
    def get_family_memberships(self, user_id: int) -> List[FamilyMember]:
        return (
            self.db.query(FamilyMember)
            .filter(FamilyMember.user_id == user_id)
            .all()
        )

    # 해당 가족의 모든 멤버 조회
    def get_family_members(self, family_id: int) -> List[FamilyMember]:
        return (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id)
            .all()
        )

    def update_user(self, user: User, nickname=None, phone=None):
        if nickname is not None:
            user.nickname = nickname
        if phone is not None:
            user.phone = phone

        self.db.commit()
        self.db.refresh(user)
        return user