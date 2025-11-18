from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_firebase_uid(self, firebase_uid: str):
        return (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

    def update_user(self, user: User, nickname=None, phone=None):
        if nickname is not None:
            user.nickname = nickname
        if phone is not None:
            user.phone = phone

        self.db.commit()
        self.db.refresh(user)
        return user