from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.notification import Notification, NotificationType
from app.models.notification_reads import NotificationRead
from app.models.family_member import FamilyMember


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    # ============================
    # 📌 알림 조회
    # ============================
    def get_notifications(
        self,
        user_id: int,
        pet_id: int | None,
        page: int,
        size: int
    ):
        # 사용자가 속한 family_id
        family_ids = (
            self.db.query(FamilyMember.family_id)
            .filter(FamilyMember.user_id == user_id)
            .subquery()
        )

        query = (
            self.db.query(Notification)
            .options(
                joinedload(Notification.related_user),
                joinedload(Notification.related_pet),
                joinedload(Notification.related_request),    # ⭐ 추가
            )
            .filter(
                (Notification.target_user_id == user_id)
                |
                ((Notification.target_user_id.is_(None)) &
                 (Notification.family_id.in_(family_ids)))
            )
        )

        if pet_id is not None:
            query = query.filter(Notification.related_pet_id == pet_id)

        query = query.order_by(Notification.created_at.asc())

        total = query.count()
        items = query.offset(page * size).limit(size).all()

        return items, total

    # ============================
    # 📌 가족 인원수
    # ============================
    def get_family_member_count(self, family_id: int) -> int:
        return (
            self.db.query(func.count(FamilyMember.user_id))
            .filter(FamilyMember.family_id == family_id)
            .scalar()
        )

    # ============================
    # 📌 읽은 사람 수
    # ============================
    def get_read_count(self, notification_id: int) -> int:
        return (
            self.db.query(NotificationRead.user_id)
            .filter(NotificationRead.notification_id == notification_id)
            .distinct()
            .count()
        )

    # ============================
    # 📌 읽음 처리
    # ============================
    def mark_as_read(self, notification_id: int, user_id: int):
        exists = (
            self.db.query(NotificationRead)
            .filter(
                NotificationRead.notification_id == notification_id,
                NotificationRead.user_id == user_id
            )
            .first()
        )

        if exists:
            return "ALREADY_READ"

        new_row = NotificationRead(
            notification_id=notification_id,
            user_id=user_id
        )
        self.db.add(new_row)
        return "OK"

    # ============================
    # 📌 단일 조회
    # ============================
    def get_notification_by_id(self, notification_id: int):
        return (
            self.db.query(Notification)
            .filter(Notification.notification_id == notification_id)
            .first()
        )

    # ============================
    # 📌 알림 생성 (모든 타입 지원)
    # ============================
    def create_notification(
        self,
        family_id: int,
        target_user_id: int | None,
        related_pet_id: int | None,
        related_user_id: int | None,
        notif_type: NotificationType,
        title: str,
        message: str,
        related_request_id: int | None = None,
    ):
        notif = Notification(
            family_id=family_id,
            target_user_id=target_user_id,
            related_pet_id=related_pet_id,
            related_user_id=related_user_id,
            related_request_id=related_request_id,
            type=notif_type,
            title=title,
            message=message,
        )
        self.db.add(notif)
        self.db.flush()

        # 개인 알림이면 자동 읽음 처리
        if target_user_id is not None:
            read = NotificationRead(
                notification_id=notif.notification_id,
                user_id=target_user_id
            )
            self.db.add(read)

        return notif

