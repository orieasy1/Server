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

    def create_user(self, firebase_uid, nickname, email, picture, sns_id):
        user = User(
            firebase_uid=firebase_uid,
            sns_id=sns_id,     # ⭐ 추가
            nickname=nickname,
            email=email,
            profile_img_url=picture
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

