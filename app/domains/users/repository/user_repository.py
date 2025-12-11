from sqlalchemy import inspect, func
from sqlalchemy.orm import Session
from typing import Iterable, List, Optional, Set

from app.models.family_member import FamilyMember
from app.models.user import User
from app.models.user_fcm_token import UserFcmToken


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------
    def _ensure_fcm_token_table(self) -> bool:
        """
        Ensure user_fcm_tokens table exists.
        """
        try:
            bind = self.db.get_bind()
            inspector = inspect(bind)
            if not inspector.has_table(UserFcmToken.__tablename__):
                # create table if missing (checkfirst avoids errors)
                UserFcmToken.__table__.create(bind=bind, checkfirst=True)
            return True
        except Exception as e:
            print(f"[FCM] Failed to ensure user_fcm_tokens table: {e}")
            return False

    # -------------------------------------------------
    # Basic user lookups
    # -------------------------------------------------

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

    # -------------------------------------------------
    # FCM token management
    # -------------------------------------------------
    def upsert_fcm_token(
        self,
        user: User,
        fcm_token: str,
        device_id: Optional[str] = None,
        platform: Optional[str] = "android",
    ):
        """
        Store/update FCM token for a user.
        Keeps legacy user.fcm_token while also maintaining per-device rows.
        """
        user.fcm_token = fcm_token

        if not fcm_token:
            return

        table_ready = self._ensure_fcm_token_table()
        if not table_ready:
            return

        # 1) If token already exists anywhere, move it to this user/device
        existing_by_token = (
            self.db.query(UserFcmToken)
            .filter(UserFcmToken.fcm_token == fcm_token)
            .first()
        )

        if existing_by_token:
            existing_by_token.user_id = user.user_id
            existing_by_token.device_id = device_id or existing_by_token.device_id
            existing_by_token.platform = platform or existing_by_token.platform
            existing_by_token.is_active = True
            existing_by_token.updated_at = func.now()
            return

        # 2) If we know device_id, update that row; else create a new one
        device_row = None
        if device_id:
            device_row = (
                self.db.query(UserFcmToken)
                .filter(
                    UserFcmToken.user_id == user.user_id,
                    UserFcmToken.device_id == device_id,
                )
                .first()
            )

        if device_row:
            device_row.fcm_token = fcm_token
            device_row.platform = platform or device_row.platform
            device_row.is_active = True
            device_row.updated_at = func.now()
        else:
            self.db.add(
                UserFcmToken(
                    user_id=user.user_id,
                    fcm_token=fcm_token,
                    device_id=device_id,
                    platform=platform or "android",
                    is_active=True,
                )
            )

    def get_active_fcm_tokens_for_users(self, user_ids: Iterable[int]) -> List[str]:
        """
        Return a de-duplicated list of active FCM tokens for the given users.
        Falls back to legacy user.fcm_token column.
        """
        ids: List[int] = list(set(user_ids))
        if not ids:
            return []

        tokens: Set[str] = set()

        # Legacy column fallback
        for (token,) in (
            self.db.query(User.fcm_token).filter(User.user_id.in_(ids)).all()
        ):
            if token:
                tokens.add(token)

        # Multi-device table
        if self._ensure_fcm_token_table():
            for (token,) in (
                self.db.query(UserFcmToken.fcm_token)
                .filter(
                    UserFcmToken.user_id.in_(ids),
                    UserFcmToken.is_active.is_(True),
                )
                .all()
            ):
                if token:
                    tokens.add(token)

        return list(tokens)

    def remove_fcm_tokens(self, tokens: Iterable[str]) -> int:
        """
        Remove/deactivate invalid tokens across both storage locations.
        Returns count of rows touched.
        """
        token_list = [t for t in tokens if t]
        if not token_list:
            return 0

        touched = 0

        # Clear legacy column matches
        users = (
            self.db.query(User)
            .filter(User.fcm_token.in_(token_list))
            .all()
        )
        for user in users:
            user.fcm_token = None
            touched += 1

        if self._ensure_fcm_token_table():
            rows = (
                self.db.query(UserFcmToken)
                .filter(UserFcmToken.fcm_token.in_(token_list))
                .all()
            )
            for row in rows:
                self.db.delete(row)
                touched += 1

        if touched:
            try:
                self.db.commit()
            except Exception as e:
                print(f"[FCM] Failed to commit token cleanup: {e}")
                self.db.rollback()

        return touched