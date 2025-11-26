# app/domains/notifications/repository/notification_repository.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.notification import Notification, NotificationType
from app.models.notification_reads import NotificationRead
from app.models.family_member import FamilyMember


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_notifications(
        self,
        user_id: int,
        pet_id: int | None,
        notif_type: str | None,
        page: int,
        size: int
    ):
        query = (
            self.db.query(Notification)
            .options(
                joinedload(Notification.related_user),
                joinedload(Notification.related_pet),
            )
        )

        # 사용자가 속한 family의 알림만 조회
        query = query.join(
            FamilyMember,
            FamilyMember.family_id == Notification.family_id
        ).filter(FamilyMember.user_id == user_id)

        # pet 필터 적용
        if pet_id is not None:
            query = query.filter(Notification.related_pet_id == pet_id)

        # type 필터 적용
        if notif_type is not None:
            try:
                t_enum = NotificationType[notif_type]
                query = query.filter(Notification.type == t_enum)
            except KeyError:
                return None, "INVALID_TYPE"

        # 카톡처럼 오래된 → 최신순 ASC 정렬
        query = query.order_by(Notification.created_at.asc())

        total_count = query.count()

        items = query.offset(page * size).limit(size).all()

        return items, total_count

    # ------------------------------------------------------
    # 📌 가족 구성원 수 (sender 포함)
    # ------------------------------------------------------
    def get_family_member_count(self, family_id: int) -> int:
        return (
            self.db.query(func.count(FamilyMember.user_id))
            .filter(FamilyMember.family_id == family_id)
            .scalar()
        )

    # ------------------------------------------------------
    # 📌 읽은 사람 수 (sender 제외)
    # ------------------------------------------------------
    def get_read_count(self, notification_id):
        return (
            self.db.query(NotificationRead.user_id)
            .filter(NotificationRead.notification_id == notification_id)
            .distinct()
            .count()
        )



    # ------------------------------------------------------
    # 📌 읽음 처리
    # ------------------------------------------------------
    def mark_as_read(self, notification_id: int, user_id: int):
        existing = (
            self.db.query(NotificationRead)
            .filter(
                NotificationRead.notification_id == notification_id,
                NotificationRead.user_id == user_id
            )
            .first()
        )

        if existing:
            return "ALREADY_READ"

        new_row = NotificationRead(
            notification_id=notification_id,
            user_id=user_id
        )

        self.db.add(new_row)
        self.db.commit()
        return "OK"
    
    # ------------------------------------------------------
    # 📌 알림 단건 조회 (읽음 처리용)
    # ------------------------------------------------------
    def get_notification_by_id(self, notification_id: int):
        return (
            self.db.query(Notification)
            .filter(Notification.notification_id == notification_id)
            .first()
        )

    
