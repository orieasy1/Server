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
    # 📌 알림 목록 조회
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

        # ----------------------------------
        # DB 조회
        # ----------------------------------
        items, total = self.repo.get_notifications(
            user_id=user.user_id,
            pet_id=pet_id,
            page=page,
            size=size
        )

        if items is None and total == "INVALID_TYPE":
            return error_response(400, "NOTIF_400", "알림 타입 오류", request.url.path)

        results = []

        for notif in items:
            # ❗ 내가 보낸 알림인지
            is_me = (notif.related_user_id == user.user_id)

            # ❗ 내가 읽었는지
            is_read = (
                self.db.query(NotificationRead)
                .filter(
                    NotificationRead.notification_id == notif.notification_id,
                    NotificationRead.user_id == user.user_id
                )
                .first() is not None
            )

            
            if notif.target_user_id is not None:
                unread_count = 0
                read_count = 1
            else:
                # ❗ family 전체 인원수
                family_count = self.repo.get_family_member_count(notif.family_id)
                # ❗ 이 알림을 읽은 사람 수
                read_count = self.repo.get_read_count(notif.notification_id)
                unread_count = family_count - read_count

            # ❗ display_time (오전/오후)
            display_time = (
                notif.created_at.strftime("%p %I:%M")
                .replace("AM", "오전")
                .replace("PM", "오후")
            )

            # ❗ 알림 타입 라벨
            display_type_label = f"[{notif.type.value}]"

            # ❗ 읽음 텍스트
            display_read_text = f"{read_count}명 읽음"

            # ❗ sender info
            sender_profile_img_url = notif.related_user.profile_img_url if notif.related_user else None
            sender_nickname = notif.related_user.nickname if notif.related_user else None

            # --------------------------------------
            # 읽음처리 (안읽었으면 기록)
            # --------------------------------------
            if notif.target_user_id is None:
                if not is_read:
                    read_obj = NotificationRead(
                        notification_id=notif.notification_id,
                        user_id=user.user_id,
                        read_at=datetime.utcnow()
                    )
                    self.db.add(read_obj)
                    self.db.commit()
                    is_read = True

                    # readable 상태 업데이트
                    read_count += 1
                    unread_count -= 1
                    display_read_text = f"{read_count}명 읽음"

            # --------------------------------------
            # 응답에 넣기 — 전 필드 포함
            # --------------------------------------
            results.append({
                "notification_id": notif.notification_id,
                "type": notif.type.value,
                "title": notif.title,
                "message": notif.message,

                "family_id": notif.family_id,
                "target_user_id": notif.target_user_id,

                # 관계
                "related_pet": notif.related_pet,
                "related_user": notif.related_user,
                "related_request_id": notif.related_request_id,
                "related_lat": float(notif.related_lat) if notif.related_lat else None,
                "related_lng": float(notif.related_lng) if notif.related_lng else None,

                # 읽음 관련
                "is_read_by_me": is_read,
                "is_me": is_me,
                "read_count": read_count,
                "unread_count": unread_count,

                # 프론트 UI
                "display_time": display_time,
                "display_type_label": display_type_label,
                "display_read_text": display_read_text,
                "sender_profile_img_url": sender_profile_img_url,
                "sender_nickname": sender_nickname,

                "created_at": notif.created_at,
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
                NotificationRead.user_id == user.user_id
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

        new_read = NotificationRead(
            notification_id=notification_id,
            user_id=user.user_id,
            read_at=datetime.utcnow()
        )
        self.db.add(new_read)
        self.db.commit()

        return {
            "success": True,
            "status": 200,
            "message": "읽음 처리 완료",
            "notification_id": notification_id,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }
        