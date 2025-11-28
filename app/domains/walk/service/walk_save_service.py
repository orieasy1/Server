from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import pytz

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.models.walk import Walk
from app.models.walk_tracking_point import WalkTrackingPoint
from app.schemas.walk.walk_save_schema import WalkSaveRequest
from app.domains.walk.repository.session_repository import SessionRepository


class WalkSaveService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)

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
            return error_response(
                401, "WALK_SAVE_401_1", "Authorization 헤더가 필요합니다.", path
            )

        if not authorization.startswith("Bearer "):
            return error_response(
                401, "WALK_SAVE_401_2",
                "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.",
                path
            )

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(
                401, "WALK_SAVE_401_2",
                "Authorization 헤더 형식이 잘못되었습니다.",
                path
            )

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return error_response(
                401, "WALK_SAVE_401_2",
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
                404, "WALK_SAVE_404_1",
                "해당 사용자를 찾을 수 없습니다.",
                path
            )

        # ============================================
        # 3) 반려동물 조회 및 권한 체크
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == body.pet_id)
            .first()
        )

        if not pet:
            return error_response(
                404, "WALK_SAVE_404_2",
                "요청하신 반려동물을 찾을 수 없습니다.",
                path
            )

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
            return error_response(
                403, "WALK_SAVE_403_1",
                "해당 반려동물의 산책 기록을 저장할 권한이 없습니다.",
                path
            )

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
                return error_response(
                    400, "WALK_SAVE_400_1",
                    "종료 시간은 시작 시간보다 이후여야 합니다.",
                    path
                )
        except ValueError as e:
            return error_response(
                400, "WALK_SAVE_400_2",
                f"날짜/시간 형식이 올바르지 않습니다. ISO 8601 형식(YYYY-MM-DDTHH:mm:ss)을 사용해주세요. {str(e)}",
                path
            )

        # ============================================
        # 5) Walk 저장
        # ============================================
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
            
            # thumbnail_image_url은 모델에 필드가 없으면 일단 저장하지 않음
            # 나중에 모델에 추가하면 활성화
            # if body.thumbnail_image_url:
            #     walk.thumbnail_image_url = body.thumbnail_image_url
            
            self.db.add(walk)
            self.db.flush()  # walk_id 확보
            
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
            return error_response(
                500, "WALK_SAVE_500_1",
                "산책 기록을 저장하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                path
            )

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
                "thumbnail_image_url": body.thumbnail_image_url,  # 요청에서 받은 값 반환
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)

