# app/domains/notifications/service/notification_service.py

from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response

from app.models.user import User
from app.models.notification_reads import NotificationRead
from app.domains.notifications.repository.notification_repository import NotificationRepository
from app.schemas.notifications.notification_schema import NotificationListResponse


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    # ============================
    # 📌 알림 목록 조회 (Personal only)
    # ============================
    def get_notifications(self, request, firebase_token, pet_id, notif_type, page, size):
        if not firebase_token:
            return error_response(401, "NOTIF_401", "Authorization 필요", request.url.path)

        decoded = verify_firebase_token(firebase_token)
        if decoded is None:
            return error_response(401, "NOTIF_401_2", "Firebase 토큰 오류", request.url.path)

        user = self.db.query(User).filter(User.firebase_uid == decoded["uid"]).first()
        if not user:
            return error_response(404, "NOTIF_404_1", "사용자 없음", request.url.path)

        # =============================
        # DB 조회 (Personal only)
        # =============================
        items, total = self.repo.get_notifications(
            user_id=user.user_id,
            pet_id=pet_id,
            notif_type=notif_type,
            page=page,
            size=size
        )

        if items is None and total == "INVALID_TYPE":
            return error_response(400, "NOTIF_400", "알림 타입 오류", request.url.path)

        results = []

        # =============================
        # 각 알림 처리
        # =============================
        for notif in items:

            # 내가 보낸 알림인지
            is_me = (notif.related_user_id == user.user_id)

            # 읽음 여부
            is_read = (
                self.db.query(NotificationRead)
                .filter(
                    NotificationRead.notification_id == notif.notification_id,
                    NotificationRead.user_id == user.user_id,
                )
                .first() is not None
            )

            # 안읽음이면 읽음 처리
            if not is_read:
                read = NotificationRead(
                    notification_id=notif.notification_id,
                    user_id=user.user_id,
                    read_at=datetime.utcnow()
                )
                self.db.add(read)
                self.db.commit()
                is_read = True

            results.append({
                "notification_id": notif.notification_id,
                "type": notif.type.value,
                "title": notif.title,
                "message": notif.message,
                "family_id": notif.family_id,
                "target_user_id": notif.target_user_id,
                "related_pet": notif.related_pet,
                "related_user": notif.related_user,
                "created_at": notif.created_at,
                "is_read_by_me": is_read,
                "is_me": is_me,
            })

        return NotificationListResponse(
            success=True,
            status=200,
            notifications=results,
            page=page,
            size=size,
            total_count=total,
            timeStamp=datetime.utcnow().isoformat(),
            path=request.url.path,
        )

    # ============================
    # 📌 읽음 처리
    # ============================
    def mark_read(self, request, firebase_token, notification_id):
        path = request.url.path

        if not firebase_token:
            return error_response(401, "NOTIF_READ_401_1", "Authorization 필요", path)

        decoded = verify_firebase_token(firebase_token)
        if decoded is None:
            return error_response(401, "NOTIF_READ_401_2", "토큰 오류", path)

        user = (
            self.db.query(User)
            .filter(User.firebase_uid == decoded["uid"])
            .first()
        )
        if not user:
            return error_response(404, "NOTIF_READ_404_1", "사용자 없음", path)

        notif = self.repo.get_notification_by_id(notification_id)
        if not notif:
            return error_response(404, "NOTIF_READ_404_2", "알림 없음", path)

        existing = (
            self.db.query(NotificationRead)
            .filter(
                NotificationRead.notification_id == notification_id,
                NotificationRead.user_id == user.user_id,
            )
            .first()
        )

        if existing:
            return {
                "success": True,
                "status": 200,
                "message": "이미 읽음",
                "notification_id": notification_id,
                "timeStamp": datetime.utcnow().isoformat(),
                "path": path
            }

        new_row = NotificationRead(
            notification_id=notification_id,
            user_id=user.user_id,
            read_at=datetime.utcnow(),
        )
        self.db.add(new_row)
        self.db.commit()

        return {
            "success": True,
            "status": 200,
            "message": "읽음 처리 완료",
            "notification_id": notification_id,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }
