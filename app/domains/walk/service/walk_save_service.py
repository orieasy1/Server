from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import pytz

from app.core.firebase import verify_firebase_token, send_push_notification_to_multiple
from app.domains.walk.exception import walk_error
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.models.walk import Walk
from app.models.photo import Photo
from app.models.walk_tracking_point import WalkTrackingPoint
from app.models.notification import NotificationType
from app.schemas.walk.walk_save_schema import WalkSaveRequest
from app.domains.walk.repository.session_repository import SessionRepository
from app.domains.notifications.repository.notification_repository import NotificationRepository
from app.domains.users.repository.user_repository import UserRepository


class WalkSaveService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.user_repo = UserRepository(db)

    def _send_walk_complete_fcm_push(
        self,
        family_id: int,
        exclude_user_id: int,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ):
        """
        가족 멤버들에게 산책 완료 FCM 푸시 알림을 발송합니다.
        산책한 본인은 제외합니다.
        """
        try:
            print(f"[FCM DEBUG] _send_walk_complete_fcm_push called: family_id={family_id}, exclude_user_id={exclude_user_id}")
            
            # 가족 멤버 조회
            family_members = (
                self.db.query(FamilyMember)
                .filter(FamilyMember.family_id == family_id)
                .all()
            )
            
            print(f"[FCM DEBUG] Family members count: {len(family_members)}")

            target_user_ids = [
                m.user_id for m in family_members if m.user_id != exclude_user_id
            ]
            fcm_tokens = self.user_repo.get_active_fcm_tokens_for_users(target_user_ids)
            print(f"[FCM DEBUG] Target user IDs: {target_user_ids}")
            token_previews = [t[:15] + "..." if t and len(t) > 15 else t for t in fcm_tokens]
            print(f"[FCM DEBUG] Collected FCM tokens: {len(fcm_tokens)} ({token_previews})")

            # FCM 푸시 발송
            if fcm_tokens:
                result = send_push_notification_to_multiple(
                    fcm_tokens=fcm_tokens,
                    title=title,
                    body=body,
                    data=data,
                )
                print(f"[FCM] Walk complete push sent: success={result['success_count']}, failure={result['failure_count']}")
                if result.get("invalid_tokens"):
                    self.user_repo.remove_fcm_tokens(result["invalid_tokens"])
            else:
                print("[FCM] No FCM tokens to send walk complete notification")

        except Exception as e:
            print(f"[FCM] Walk complete push error: {e}")
            import traceback
            traceback.print_exc()

    def save_walk(
        self,
        request: Request,
        authorization: Optional[str],
        body: WalkSaveRequest,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return walk_error("WALK_SAVE_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_SAVE_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return walk_error("WALK_SAVE_401_2", path)

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return walk_error("WALK_SAVE_401_2", path)

        firebase_uid = decoded.get("uid")

        # ============================================
        # 2) 사용자 조회
        # ============================================
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            return walk_error("WALK_SAVE_404_1", path)

        # ============================================
        # 3) 반려동물 조회 및 권한 체크
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == body.pet_id)
            .first()
        )

        if not pet:
            return walk_error("WALK_SAVE_404_2", path)

        # 권한 체크
        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return walk_error("WALK_SAVE_403_1", path)

        # ============================================
        # 4) 날짜/시간 파싱
        # ============================================
        try:
            # ISO 8601 형식 파싱 (YYYY-MM-DDTHH:mm:ss)
            start_time = datetime.fromisoformat(body.start_time.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(body.end_time.replace('Z', '+00:00'))
            
            # UTC로 변환 (로컬 시간이면 UTC로 변환)
            if start_time.tzinfo is None:
                # 타임존 정보가 없으면 UTC로 가정
                start_time = pytz.UTC.localize(start_time)
            else:
                start_time = start_time.astimezone(pytz.UTC)
            
            if end_time.tzinfo is None:
                end_time = pytz.UTC.localize(end_time)
            else:
                end_time = end_time.astimezone(pytz.UTC)
            
            # end_time이 start_time보다 이후인지 확인
            if end_time <= start_time:
                return walk_error("WALK_SAVE_400_1", path)
        except ValueError as e:
            return walk_error("WALK_SAVE_400_2", path)

        # ============================================
        # 5) Walk 저장
        # ============================================
        thumbnail_url = None
        try:
            walk = Walk(
                pet_id=body.pet_id,
                user_id=user.user_id,
                start_time=start_time,
                end_time=end_time,
                duration_min=body.duration_min,
                distance_km=body.distance_km,
                calories=body.calories,
                weather_status=body.weather_status,
                weather_temp_c=body.weather_temp_c,
            )

            self.db.add(walk)
            self.db.flush()  # walk_id 확보

            if body.thumbnail_image_url:
                photo = Photo(
                    walk_id=walk.walk_id,
                    image_url=body.thumbnail_image_url,
                    uploaded_by=user.user_id,
                    caption=None,
                )
                self.db.add(photo)
                thumbnail_url = body.thumbnail_image_url
            
            # 경로 포인트 저장
            if body.route_points:
                for point_dto in body.route_points:
                    try:
                        point_timestamp = datetime.fromisoformat(
                            point_dto.timestamp.replace('Z', '+00:00')
                        )
                        if point_timestamp.tzinfo is None:
                            point_timestamp = pytz.UTC.localize(point_timestamp)
                        else:
                            point_timestamp = point_timestamp.astimezone(pytz.UTC)
                    except ValueError:
                        # 타임스탬프 파싱 실패 시 스킵
                        continue
                    
                    tracking_point = WalkTrackingPoint(
                        walk_id=walk.walk_id,
                        latitude=point_dto.latitude,
                        longitude=point_dto.longitude,
                        timestamp=point_timestamp,
                    )
                    self.db.add(tracking_point)
            
            self.db.commit()
            self.db.refresh(walk)
            
        except Exception as e:
            print("WALK_SAVE_ERROR:", e)
            self.db.rollback()
            return walk_error("WALK_SAVE_500_1", path)

        # ============================================
        # 5-1) 산책 완료 알림 생성 + FCM 푸시 발송
        # ============================================
        try:
            # 산책 결과 정보
            walk_summary = ""
            if body.duration_min:
                walk_summary += f"{body.duration_min}분"
            if body.distance_km:
                walk_summary += f" {body.distance_km:.1f}km"
            
            notification_message = f"{user.nickname}님이 {pet.name}와 산책을 마쳤습니다."
            if walk_summary.strip():
                notification_message += f" ({walk_summary.strip()})"
            
            # 알림 생성 (family 전체)
            self.notification_repo.create_notification(
                family_id=pet.family_id,
                target_user_id=None,  # 가족 전체에게 보여주는 공용 알림
                related_pet_id=pet.pet_id,
                related_user_id=user.user_id,
                notif_type=NotificationType.ACTIVITY_END,
                title="산책 완료",
                message=notification_message,
            )
            self.db.commit()
            
            # 🔔 FCM 푸시 알림 발송 (산책한 본인 제외)
            self._send_walk_complete_fcm_push(
                family_id=pet.family_id,
                exclude_user_id=user.user_id,
                title="✅ 산책 완료",
                body=notification_message,
                data={
                    "type": "WALK_END",
                    "walk_id": walk.walk_id,
                    "pet_id": pet.pet_id,
                    "pet_name": pet.name or "",
                    "user_nickname": user.nickname or "",
                    "duration_min": str(body.duration_min) if body.duration_min else "",
                    "distance_km": str(body.distance_km) if body.distance_km else "",
                },
            )
            
        except Exception as e:
            print("WALK_SAVE_NOTIFICATION_ERROR:", e)
            import traceback
            traceback.print_exc()
            # 알림 실패해도 산책 저장은 성공으로 처리

        # ============================================
        # 6) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 200,
            "walk": {
                "walk_id": walk.walk_id,
                "pet_id": walk.pet_id,
                "user_id": walk.user_id,
                "start_time": walk.start_time.isoformat() if walk.start_time else None,
                "end_time": walk.end_time.isoformat() if walk.end_time else None,
                "duration_min": walk.duration_min,
                "distance_km": float(walk.distance_km) if walk.distance_km is not None else None,
                "calories": float(walk.calories) if walk.calories is not None else None,
                "weather_status": walk.weather_status,
                "weather_temp_c": float(walk.weather_temp_c) if walk.weather_temp_c is not None else None,
                "thumbnail_image_url": thumbnail_url,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)

    def notify_walk_start(
        self,
        request,
        authorization: Optional[str],
        pet_id: int,
    ):
        """
        산책 시작 시 가족 멤버들에게 알림을 전송합니다.
        """
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return walk_error("WALK_NOTIFY_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_NOTIFY_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return walk_error("WALK_NOTIFY_401_2", path)

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return walk_error("WALK_NOTIFY_401_2", path)

        firebase_uid = decoded.get("uid")

        # ============================================
        # 2) 사용자 조회
        # ============================================
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            return walk_error("WALK_NOTIFY_404_1", path)

        # ============================================
        # 3) 반려동물 조회 및 권한 체크
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == pet_id)
            .first()
        )

        if not pet:
            return walk_error("WALK_NOTIFY_404_2", path)

        # 권한 체크
        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return walk_error("WALK_NOTIFY_403_1", path)

        # ============================================
        # 4) 산책 시작 알림 생성 + FCM 푸시 발송
        # ============================================
        try:
            notification_message = f"{user.nickname}님이 {pet.name}와 산책을 시작했습니다."
            
            # 알림 생성 (family 전체)
            self.notification_repo.create_notification(
                family_id=pet.family_id,
                target_user_id=None,  # 가족 전체에게 보여주는 공용 알림
                related_pet_id=pet.pet_id,
                related_user_id=user.user_id,
                notif_type=NotificationType.ACTIVITY_START,
                title="산책 시작",
                message=notification_message,
            )
            self.db.commit()
            
            # 🔔 FCM 푸시 알림 발송 (산책 시작한 본인 제외)
            self._send_walk_complete_fcm_push(
                family_id=pet.family_id,
                exclude_user_id=user.user_id,
                title="🚶 산책 시작",
                body=notification_message,
                data={
                    "type": "WALK_START",
                    "pet_id": pet.pet_id,
                    "pet_name": pet.name or "",
                    "user_nickname": user.nickname or "",
                },
            )
            
            print(f"[WALK_START] Notification sent for pet {pet.pet_id} by user {user.user_id}")
            
        except Exception as e:
            print("WALK_START_NOTIFICATION_ERROR:", e)
            import traceback
            traceback.print_exc()
            return walk_error("WALK_NOTIFY_500_1", path)

        # ============================================
        # 5) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 200,
            "message": "산책 시작 알림이 전송되었습니다.",
            "pet_id": pet.pet_id,
            "pet_name": pet.name,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)

