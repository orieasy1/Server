from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
import pytz

from app.core.firebase import verify_firebase_token, send_push_notification_to_multiple
from app.domains.walk.exception import walk_error
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.models.notification import NotificationType
from app.domains.walk.repository.session_repository import SessionRepository
from app.domains.notifications.repository.notification_repository import NotificationRepository
from app.domains.users.repository.user_repository import UserRepository
from app.schemas.walk.session_schema import WalkStartRequest, WalkTrackRequest, WalkEndRequest


class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.user_repo = UserRepository(db)

    def _send_walk_fcm_push(
        self,
        family_id: int,
        exclude_user_id: int,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ):
        """
        가족 멤버들에게 산책 관련 FCM 푸시 알림을 발송합니다.
        산책을 시작/종료한 본인은 제외합니다.
        """
        try:
            print(f"[FCM DEBUG] _send_walk_fcm_push called: family_id={family_id}, exclude_user_id={exclude_user_id}")
            
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
                print(f"[FCM] Walk push sent: success={result['success_count']}, failure={result['failure_count']}")
                if result.get("invalid_tokens"):
                    self.user_repo.remove_fcm_tokens(result["invalid_tokens"])
            else:
                print("[FCM] No FCM tokens to send walk notification")

        except Exception as e:
            print(f"[FCM] Walk push error: {e}")
            import traceback
            traceback.print_exc()

    def start_walk(
        self,
        request: Request,
        authorization: Optional[str],
        body: WalkStartRequest,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return walk_error("WALK_START_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_START_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return walk_error("WALK_START_401_2", path)

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return walk_error("WALK_START_401_2", path)

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
            return walk_error("WALK_START_404_1", path)

        # ============================================
        # 3) Body 유효성 검사
        # ============================================
        # 3-1) pet_id 필수 체크
        if body.pet_id is None:
            return walk_error("WALK_START_400_1", path)

        # 3-2) start_lat / start_lng 짝 맞춤 체크
        has_lat = body.start_lat is not None
        has_lng = body.start_lng is not None
        
        if has_lat != has_lng:
            return walk_error("WALK_START_400_2", path)

        # ============================================
        # 4) 반려동물 조회
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == body.pet_id)
            .first()
        )

        if not pet:
            return walk_error("WALK_START_404_2", path)

        # ============================================
        # 5) 권한 체크 (family_members 확인)
        # ============================================
        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return walk_error("WALK_START_403_1", path)

        # ============================================
        # 6) 진행 중인 산책 체크
        # ============================================
        try:
            ongoing_walk = self.session_repo.get_ongoing_walk_by_pet_id(body.pet_id)
            
            if ongoing_walk:
                return walk_error("WALK_START_409_1", path)
        except Exception as e:
            print("ONGOING_WALK_CHECK_ERROR:", e)
            return walk_error("WALK_START_500_1", path)

        # ============================================
        # 7) 산책 세션 생성
        # ============================================
        try:
            start_time = datetime.utcnow()

            # 산책 세션 생성
            walk = self.session_repo.create_walk(
                pet_id=body.pet_id,
                user_id=user.user_id,
                start_time=start_time,
            )

            # 첫 위치 저장
            if has_lat and has_lng:
                self.session_repo.create_tracking_point(
                    walk_id=walk.walk_id,
                    latitude=body.start_lat,
                    longitude=body.start_lng,
                    timestamp=start_time,
                )

            # 🔥 walk 생성은 반드시 성공해야 하므로 먼저 commit
            self.db.commit()
            self.db.refresh(walk)

        except Exception as e:
            print("WALK_CREATE_ERROR:", e)
            self.db.rollback()
            return walk_error("WALK_START_500_1", path)

        # ============================================
        # 7-1) 산책 시작 알림 생성 (FAMILY 기준 1개) + FCM 푸시
        # ============================================
        try:
            # 🔥 기존 중복 알림 방지 로직: 시작시간 이후 이미 생성된 알림이 있는지 확인
            existing = self.notification_repo.check_existing_activity_notification(
                family_id=pet.family_id,
                related_pet_id=pet.pet_id,
                related_user_id=user.user_id,
                notif_type=NotificationType.ACTIVITY_START,
                since_time=walk.start_time,
            )

            if existing:
                print("SKIP: Duplicate ACTIVITY_START notification")
            else:
                self.notification_repo.create_notification(
                    family_id=pet.family_id,
                    target_user_id=None,  # ⭐ 가족 전체에게 보여주는 공용 알림
                    related_pet_id=pet.pet_id,
                    related_user_id=user.user_id,
                    notif_type=NotificationType.ACTIVITY_START,
                    title="산책 시작",
                    message=f"{user.nickname}님이 {pet.name}와 산책을 시작했습니다.",
                )
                self.db.commit()

                # 🔔 FCM 푸시 알림 발송 (산책 시작한 본인 제외)
                self._send_walk_fcm_push(
                    family_id=pet.family_id,
                    exclude_user_id=user.user_id,
                    title="🚶 산책 시작",
                    body=f"{user.nickname}님이 {pet.name}와 산책을 시작했습니다.",
                    data={
                        "type": "WALK_START",
                        "walk_id": walk.walk_id,
                        "pet_id": pet.pet_id,
                        "pet_name": pet.name or "",
                        "user_nickname": user.nickname or "",
                    },
                )

        except Exception as e:
            print("NOTIFICATION_START_ERROR:", e)
            self.db.rollback()



        # ============================================
        # 8) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 201,
            "walk": {
                "walk_id": walk.walk_id,
                "pet_id": walk.pet_id,
                "user_id": walk.user_id,
                "start_time": walk.start_time.isoformat() if walk.start_time else None,
                "end_time": walk.end_time.isoformat() if walk.end_time else None,
                "duration_min": walk.duration_min,
                "distance_km": float(walk.distance_km) if walk.distance_km else None,
                "calories": float(walk.calories) if walk.calories else None,
                "weather_status": walk.weather_status,
                "weather_temp_c": float(walk.weather_temp_c) if walk.weather_temp_c else None,
                "thumbnail_image_url": None,
                "created_at": walk.created_at.isoformat() if walk.created_at else None,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=201, content=encoded)

    def track_walk(
        self,
        request: Request,
        authorization: Optional[str],
        walk_id: int,
        body: WalkTrackRequest,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return error_response(
                401, "WALK_POINT_401_1", "Authorization 헤더가 필요합니다.", path
            )

        if not authorization.startswith("Bearer "):
            return error_response(
                401, "WALK_POINT_401_2",
                "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.",
                path
            )

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(
                401, "WALK_POINT_401_2",
                "Authorization 헤더 형식이 잘못되었습니다.",
                path
            )

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return error_response(
                401, "WALK_POINT_401_2",
                "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.",
                path
            )

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
            return error_response(
                404, "WALK_POINT_404_1",
                "해당 사용자를 찾을 수 없습니다.",
                path
            )

        # ============================================
        # 3) Body 유효성 검사
        # ============================================
        # 3-1) latitude, longitude 필수 체크
        if body.latitude is None or body.longitude is None:
            return error_response(
                400, "WALK_POINT_400_1",
                "latitude와 longitude는 필수 값입니다.",
                path
            )

        # 3-2) 위도/경도 형식 및 범위 체크
        try:
            latitude = float(body.latitude)
            longitude = float(body.longitude)
            
            # 위도: -90 ~ 90
            # 경도: -180 ~ 180
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return error_response(
                    400, "WALK_POINT_400_2",
                    "위도 또는 경도 값이 올바르지 않습니다.",
                    path
                )
        except (ValueError, TypeError):
            return error_response(
                400, "WALK_POINT_400_2",
                "위도 또는 경도 값이 올바르지 않습니다.",
                path
            )

        # 3-3) timestamp 파싱
        try:
            timestamp = datetime.fromisoformat(body.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # ISO 형식이 아니면 서버 시간 사용
            timestamp = datetime.utcnow()

        # ============================================
        # 4) 산책 세션 조회
        # ============================================
        try:
            walk = self.session_repo.get_walk_by_walk_id(walk_id)
            
            if not walk:
                return error_response(
                    404, "WALK_POINT_404_2",
                    "요청하신 산책 세션을 찾을 수 없습니다.",
                    path
                )
        except Exception as e:
            print("WALK_QUERY_ERROR:", e)
            return error_response(
                500, "WALK_POINT_500_1",
                "산책 위치 정보를 저장하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                path
            )

        # ============================================
        # 5) 산책 종료 여부 체크
        # ============================================
        if walk.end_time is not None:
            return error_response(
                409, "WALK_POINT_409_1",
                "종료된 산책 세션에는 위치 정보를 기록할 수 없습니다.",
                path
            )

        # ============================================
        # 6) 권한 체크 (family_members 확인)
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == walk.pet_id)
            .first()
        )

        if not pet:
            return error_response(
                404, "WALK_POINT_404_2",
                "요청하신 산책 세션을 찾을 수 없습니다.",
                path
            )

        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return error_response(
                403, "WALK_POINT_403_1",
                "해당 산책의 위치 정보를 기록할 권한이 없습니다.",
                path
            )

        # ============================================
        # 7) 위치 정보 저장
        # ============================================
        try:
            point = self.session_repo.create_tracking_point(
                walk_id=walk_id,
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
            )
            
            self.db.commit()
            self.db.refresh(point)

        except Exception as e:
            print("TRACKING_POINT_CREATE_ERROR:", e)
            self.db.rollback()
            return error_response(
                500, "WALK_POINT_500_1",
                "산책 위치 정보를 저장하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                path
            )

        # ============================================
        # 8) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 201,
            "point": {
                "point_id": point.point_id,
                "walk_id": point.walk_id,
                "latitude": float(point.latitude),
                "longitude": float(point.longitude),
                "timestamp": point.timestamp.isoformat() if point.timestamp else None,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=201, content=encoded)

    def end_walk(
        self,
        request: Request,
        authorization: Optional[str],
        walk_id: int,
        body: WalkEndRequest,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return error_response(401, "WALK_END_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(
                401, "WALK_END_401_2",
                "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.",
                path
            )

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(
                401, "WALK_END_401_2",
                "Authorization 헤더 형식이 잘못되었습니다.",
                path
            )

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(
                401, "WALK_END_401_2",
                "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.",
                path
            )

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
            return error_response(
                404, "WALK_END_404_1",
                "해당 사용자를 찾을 수 없습니다.",
                path
            )

        # ============================================
        # 3) 산책 세션 조회
        # ============================================
        try:
            walk = self.session_repo.get_walk_by_walk_id(walk_id)
            if not walk:
                return error_response(404, "WALK_END_404_2", "요청하신 산책 세션을 찾을 수 없습니다.", path)
        except Exception as e:
            print("WALK_QUERY_ERROR:", e)
            return error_response(500, "WALK_END_500_1", "산책을 종료하는 중 오류가 발생했습니다.", path)

        # ============================================
        # 4) 이미 종료된 산책인지 체크
        # ============================================
        if walk.end_time is not None:
            return error_response(409, "WALK_END_409_1", "이미 종료된 산책 세션입니다.", path)

        # ============================================
        # 5) family 권한 체크
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == walk.pet_id)
            .first()
        )

        if not pet:
            return error_response(404, "WALK_END_404_2", "요청하신 산책 세션을 찾을 수 없습니다.", path)

        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return error_response(403, "WALK_END_403_1", "해당 산책을 종료할 권한이 없습니다.", path)

        # ============================================
        # 6) Body 값 검증
        # ============================================
        # distance
        distance_km = None
        if body.total_distance_km is not None:
            try:
                distance_km = float(body.total_distance_km)
                if distance_km < 0:
                    return error_response(400, "WALK_END_400_1", "총 이동 거리 값이 올바르지 않습니다.", path)
            except:
                return error_response(400, "WALK_END_400_1", "총 이동 거리 값이 올바르지 않습니다.", path)

        # duration
        duration_min = None
        if body.total_duration_min is not None:
            try:
                duration_min = int(body.total_duration_min)
                if duration_min < 0:
                    return error_response(400, "WALK_END_400_2", "총 산책 시간 값이 올바르지 않습니다.", path)
            except:
                return error_response(400, "WALK_END_400_2", "총 산책 시간 값이 올바르지 않습니다.", path)

        # route_data
        route_data_dict = None
        if body.route_data is not None:
            route_data_dict = (
                body.route_data.model_dump()
                if hasattr(body.route_data, "model_dump")
                else dict(body.route_data)
            )

        # ============================================
        # 7) 산책 종료 처리 (+ 칼로리 계산)
        # ============================================
        try:
            end_time = datetime.utcnow()

            # ⭐ 칼로리 계산 로직 (MET=3 고정)
            calories = None
            if duration_min and distance_km:
                pet_weight = pet.weight if pet.weight else 5  # weight 없으면 디폴트 5kg
                MET = 3.0
                calories = pet_weight * 1.036 * duration_min * MET / 60

            updated_walk = self.session_repo.end_walk(
                walk=walk,
                end_time=end_time,
                duration_min=duration_min,
                distance_km=distance_km,
                last_lat=body.last_lat,
                last_lng=body.last_lng,
                route_data=route_data_dict,
            )

            updated_walk.calories = calories

            # ============================================
            # 7-1) activity_stats 업데이트
            # ============================================
            activity_stat = None
            if distance_km and duration_min:
                kst = pytz.timezone("Asia/Seoul")
                stat_date = datetime.now(kst).date()

                activity_stat = self.session_repo.get_or_create_activity_stat(
                    pet_id=walk.pet_id,
                    stat_date=stat_date,
                )

                self.session_repo.update_activity_stat(
                    stat=activity_stat,
                    distance_km=distance_km,
                    duration_min=duration_min,
                )

            # DB Commit
            self.db.commit()
            self.db.refresh(updated_walk)
            if activity_stat:
                self.db.refresh(activity_stat)

        except Exception as e:
            print("WALK_END_ERROR:", e)
            self.db.rollback()
            return error_response(500, "WALK_END_500_1", "산책을 종료하는 중 오류가 발생했습니다.", path)

        # ============================================
        # 8) 알림 생성 (FAMILY 전체) + FCM 푸시
        # ============================================
        try:
            existing = self.notification_repo.check_existing_activity_notification(
                family_id=pet.family_id,
                related_pet_id=pet.pet_id,
                related_user_id=user.user_id,
                notif_type=NotificationType.ACTIVITY_END,
                since_time=walk.start_time,
            )

            if not existing:
                self.notification_repo.create_notification(
                    family_id=pet.family_id,
                    target_user_id=None,  # ⭐ 가족 전체에게 보여주는 공용 알림
                    related_pet_id=pet.pet_id,
                    related_user_id=user.user_id,
                    notif_type=NotificationType.ACTIVITY_END,
                    title="산책 종료",
                    message=f"{user.nickname}님이 {pet.name}와 산책을 종료했습니다.",
                )
                self.db.commit()

                # 🔔 FCM 푸시 알림 발송 (산책 종료한 본인 제외)
                # 산책 결과 정보 포함
                walk_summary = ""
                if duration_min:
                    walk_summary += f"{duration_min}분"
                if distance_km:
                    walk_summary += f" {distance_km:.1f}km"
                
                push_body = f"{user.nickname}님이 {pet.name}와 산책을 마쳤습니다."
                if walk_summary:
                    push_body += f" ({walk_summary.strip()})"

                self._send_walk_fcm_push(
                    family_id=pet.family_id,
                    exclude_user_id=user.user_id,
                    title="✅ 산책 종료",
                    body=push_body,
                    data={
                        "type": "WALK_END",
                        "walk_id": updated_walk.walk_id,
                        "pet_id": pet.pet_id,
                        "pet_name": pet.name or "",
                        "user_nickname": user.nickname or "",
                        "duration_min": str(duration_min) if duration_min else "",
                        "distance_km": str(distance_km) if distance_km else "",
                    },
                )

        except Exception as e:
            print("NOTIFICATION_END_ERROR:", e)
            self.db.rollback()

        # ============================================
        # 9) 응답 생성
        # ============================================
        route_data_response = route_data_dict if route_data_dict else None

        response_content = {
            "success": True,
            "status": 200,
            "walk": {
                "walk_id": updated_walk.walk_id,
                "pet_id": updated_walk.pet_id,
                "user_id": updated_walk.user_id,
                "start_time": updated_walk.start_time.isoformat(),
                "end_time": updated_walk.end_time.isoformat(),
                "duration_min": updated_walk.duration_min,
                "distance_km": float(updated_walk.distance_km) if updated_walk.distance_km else None,
                "calories": float(updated_walk.calories) if updated_walk.calories else None,
                "last_lat": body.last_lat,
                "last_lng": body.last_lng,
                "route_data": route_data_response,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        if activity_stat:
            response_content["activity_stats"] = {
                "date": activity_stat.date.isoformat(),
                "pet_id": activity_stat.pet_id,
                "total_walks": activity_stat.total_walks,
                "total_distance_km": float(activity_stat.total_distance_km),
                "total_duration_min": activity_stat.total_duration_min,
                "avg_speed_kmh": float(activity_stat.avg_speed_kmh)
                if activity_stat.avg_speed_kmh else None,
            }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)
