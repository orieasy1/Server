from sqlalchemy.orm import Session
from app.models.user import User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_firebase_uid(self, firebase_uid: str):
        return (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

    def create_user(self, firebase_uid: str, nickname: str, email: str | None, picture: str | None):
        new_user = User(
            firebase_uid=firebase_uid,
            nickname=nickname,
            email=email,
            profile_img_url=picture
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
