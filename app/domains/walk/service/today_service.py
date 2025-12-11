from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import pytz

from app.core.firebase import verify_firebase_token
from app.domains.walk.exception import walk_error
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.domains.walk.repository.today_repository import TodayRepository


class TodayService:
    def __init__(self, db: Session):
        self.db = db
        self.today_repo = TodayRepository(db)

    def get_today_walks(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: int,
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return walk_error("WALK_TODAY_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_TODAY_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return walk_error("WALK_TODAY_401_2", path)

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return walk_error("WALK_TODAY_401_2", path)

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
            return walk_error("WALK_TODAY_404_1", path)

        # ============================================
        # 3) 반려동물 조회
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == pet_id)
            .first()
        )

        if not pet:
            return walk_error("WALK_TODAY_404_2", path)

        # ============================================
        # 4) 권한 체크 (family_members 확인)
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
            return walk_error("WALK_TODAY_403_1", path)

        # ============================================
        # 5) 오늘 날짜 계산 (서버 타임존 기준, KST UTC+9)
        # ============================================
        try:
            # 한국 시간대 설정
            kst = pytz.timezone('Asia/Seoul')
            now_kst = datetime.now(kst)
            
            # 오늘 날짜의 시작과 끝 시간 계산 (KST 기준)
            today_start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end_kst = now_kst.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # UTC로 변환 (DB에 저장된 시간이 UTC일 수 있으므로)
            today_start_utc = today_start_kst.astimezone(pytz.UTC)
            today_end_utc = today_end_kst.astimezone(pytz.UTC)
            
            # 날짜 문자열 (YYYY-MM-DD)
            today_date_str = now_kst.date().isoformat()

        except Exception as e:
            print("DATE_CALCULATION_ERROR:", e)
            return walk_error("WALK_TODAY_500_1", path)

        # ============================================
        # 6) 오늘 산책 현황 조회
        # ============================================
        try:
            total_walks, total_duration_min, total_distance_km, current_walk_order, has_ongoing_walk = (
                self.today_repo.get_today_walks_stats(
                    pet_id=pet_id,
                    today_start=today_start_utc,
                    today_end=today_end_utc
                )
            )

        except Exception as e:
            print("WALK_STATS_QUERY_ERROR:", e)
            return walk_error("WALK_TODAY_500_1", path)

        # ============================================
        # 7) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 200,
            "today": {
                "pet_id": pet_id,
                "date": today_date_str,
                "total_walks": total_walks,
                "total_duration_min": total_duration_min,
                "total_distance_km": round(total_distance_km, 2),
                "current_walk_order": current_walk_order,
                "has_ongoing_walk": has_ongoing_walk
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=200, content=encoded)

