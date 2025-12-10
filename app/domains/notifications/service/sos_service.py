# app/domains/notifications/service/sos_service.py

from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.firebase import verify_firebase_token, send_push_notification_to_multiple
from app.core.error_handler import error_response

from app.models.user import User
from app.models.family_member import FamilyMember
from app.models.notification import Notification, NotificationType

from app.schemas.notifications.sos_schema import SosRequestSchema, SosResponseSchema


class SosService:
    def __init__(self, db: Session):
        self.db = db

    def send_sos(
        self,
        request: Request,
        firebase_token: str | None,
        body: SosRequestSchema
    ):
        """
        SOS 알림을 가족 전원에게 전송합니다.
        """
        path = request.url.path

        # 1. 인증 확인
        if not firebase_token:
            return error_response(401, "SOS_401_1", "Authorization 필요", path)

        decoded = verify_firebase_token(firebase_token)
        if decoded is None:
            return error_response(401, "SOS_401_2", "Firebase 토큰 오류", path)

        # 2. 사용자 조회
        user = self.db.query(User).filter(User.firebase_uid == decoded["uid"]).first()
        if not user:
            return error_response(404, "SOS_404_1", "사용자 없음", path)

        # 3. 사용자가 속한 가족 찾기
        my_family_member = (
            self.db.query(FamilyMember)
            .filter(FamilyMember.user_id == user.user_id)
            .first()
        )

        if not my_family_member:
            return error_response(404, "SOS_404_2", "가족 그룹 없음", path)

        family_id = my_family_member.family_id

        # 4. 같은 가족의 다른 멤버들 조회 (자신 제외)
        family_members = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id != user.user_id
            )
            .all()
        )

        # 5. 가족 멤버들의 FCM 토큰 수집
        member_user_ids = [fm.user_id for fm in family_members]
        family_users = (
            self.db.query(User)
            .filter(User.user_id.in_(member_user_ids))
            .all()
        )

        fcm_tokens = [u.fcm_token for u in family_users if u.fcm_token]

        # 6. 알림 DB 저장
        sos_message = body.message if body.message else f"{user.nickname}님이 긴급 도움을 요청했습니다!"
        
        notification = Notification(
            family_id=family_id,
            target_user_id=None,  # 가족 전체
            related_user_id=user.user_id,
            related_pet_id=None,
            type=NotificationType.SOS,
            title="🚨 긴급 SOS 알림",
            message=sos_message,
            related_lat=Decimal(str(body.latitude)) if body.latitude else None,
            related_lng=Decimal(str(body.longitude)) if body.longitude else None,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # 7. FCM 푸시 알림 전송
        notified_count = 0
        if fcm_tokens:
            push_data = {
                "type": "SOS",
                "notification_id": str(notification.notification_id),
                "sender_id": str(user.user_id),
                "sender_name": user.nickname,
            }
            
            if body.latitude and body.longitude:
                push_data["latitude"] = str(body.latitude)
                push_data["longitude"] = str(body.longitude)

            result = send_push_notification_to_multiple(
                fcm_tokens=fcm_tokens,
                title="🚨 긴급 SOS 알림",
                body=sos_message,
                data=push_data
            )
            notified_count = result.get("success_count", 0)

        return SosResponseSchema(
            success=True,
            status=200,
            message="SOS 알림이 전송되었습니다.",
            notification_id=notification.notification_id,
            notified_count=notified_count,
            timeStamp=datetime.utcnow().isoformat(),
            path=path
        )

