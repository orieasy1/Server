from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pytz

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.domains.record.repository.stats_repository import StatsRepository


class ActivityStatsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StatsRepository(db)

    def _calc_range(self, period: str, date_str: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> tuple[datetime, datetime, str, str, int]:
        kst = pytz.timezone('Asia/Seoul')
        if period not in ["day", "week", "month", "all"]:
            raise ValueError("PERIOD")

        if period == "all":
            # very wide range
            start_kst = kst.localize(datetime(1970, 1, 1))
            end_kst = kst.localize(datetime(2999, 12, 31, 23, 59, 59, 999999))
            total_days = 0
        else:
            base_date = None
            if date_str:
                base_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                # date가 없을 때 기본값 설정
                # period=day: 오늘 날짜 사용
                # period=week: 오늘 날짜 기준으로 이번 주 시작일 계산 (아래 로직에서 처리)
                # period=month: 오늘 날짜 기준으로 이번 달 1일 계산 (아래 로직에서 처리)
                base_date = datetime.now(kst).date()
                base_date = datetime(base_date.year, base_date.month, base_date.day)
            if isinstance(base_date, datetime):
                base_kst = kst.localize(base_date)
            else:
                base_kst = kst.localize(datetime.combine(base_date, datetime.min.time()))

            if period == "day":
                start_kst = base_kst.replace(hour=0, minute=0, second=0, microsecond=0)
                end_kst = base_kst.replace(hour=23, minute=59, second=59, microsecond=999999)
                total_days = 1
            elif period == "week":
                # assume week starts Monday
                weekday = base_kst.weekday()  # Monday=0
                start_kst = (base_kst - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_kst = (start_kst + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
                total_days = 7
            elif period == "month":
                start_kst = base_kst.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                # next month
                if start_kst.month == 12:
                    next_month = start_kst.replace(year=start_kst.year + 1, month=1, day=1)
                else:
                    next_month = start_kst.replace(month=start_kst.month + 1, day=1)
                end_kst = (next_month - timedelta(seconds=1)).replace(microsecond=999999)
                total_days = (end_kst.date() - start_kst.date()).days + 1

        # override by explicit range
        if start_date:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            start_kst = kst.localize(sd.replace(hour=0, minute=0, second=0, microsecond=0))
        if end_date:
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            end_kst = kst.localize(ed.replace(hour=23, minute=59, second=59, microsecond=999999))
        if start_kst > end_kst:
            raise ValueError("RANGE")

        start_utc = start_kst.astimezone(pytz.UTC)
        end_utc = end_kst.astimezone(pytz.UTC)
        return start_utc, end_utc, start_kst.date().isoformat(), end_kst.date().isoformat(), total_days

    def get_stats(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: Optional[int],
        period: Optional[str],
        date: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        path = request.url.path

        # 1) Authorization
        if authorization is None:
            return error_response(401, "ACTIVITY_401_1", "Authorization 헤더가 필요합니다.", path)
        if not authorization.startswith("Bearer "):
            return error_response(401, "ACTIVITY_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)
        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "ACTIVITY_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)
        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "ACTIVITY_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        # 2) Required params
        if pet_id is None:
            return error_response(400, "ACTIVITY_400_1", "pet_id 쿼리 파라미터는 필수입니다.", path)
        if period is None or period not in ["day", "week", "month", "all"]:
            return error_response(400, "ACTIVITY_400_2", "period는 'day', 'week', 'month', 'all' 중 하나여야 합니다.", path)

        # 3) User and permission
        firebase_uid = decoded.get("uid")
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "ACTIVITY_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == pet_id)
            .first()
        )
        if not pet:
            return error_response(404, "ACTIVITY_404_2", "요청하신 반려동물을 찾을 수 없습니다.", path)

        fm: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == pet.family_id, FamilyMember.user_id == user.user_id)
            .first()
        )
        if not fm:
            return error_response(403, "ACTIVITY_403_1", "해당 반려동물의 활동 기록을 조회할 권한이 없습니다.", path)

        # 4) Date range
        try:
            start_utc, end_utc, start_str, end_str, total_days_hint = self._calc_range(period, date, start_date, end_date)
        except ValueError as e:
            msg = str(e)
            if msg == "PERIOD":
                return error_response(400, "ACTIVITY_400_2", "period는 'day', 'week', 'month', 'all' 중 하나여야 합니다.", path)
            elif msg == "RANGE":
                return error_response(400, "ACTIVITY_400_4", "start_date는 end_date보다 이후일 수 없습니다.", path)
            else:
                return error_response(400, "ACTIVITY_400_3", "date, start_date, end_date는 'YYYY-MM-DD' 형식이어야 합니다.", path)
        except Exception:
            return error_response(400, "ACTIVITY_400_3", "date, start_date, end_date는 'YYYY-MM-DD' 형식이어야 합니다.", path)

        # 5) Aggregate
        try:
            daily = self.repo.aggregate_daily(pet_id, start_utc, end_utc)
        except Exception as e:
            print("ACTIVITY_AGG_ERROR:", e)
            return error_response(500, "ACTIVITY_500_1", "활동 통계를 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", path)

        # build a complete date map
        kst = pytz.timezone('Asia/Seoul')
        start_kst = datetime.fromisoformat(start_str)
        end_kst = datetime.fromisoformat(end_str)
        num_days = (end_kst - start_kst).days + 1
        date_to_point: Dict[str, Dict] = {}
        for i in range(num_days):
            d = (start_kst + timedelta(days=i)).date().isoformat()
            date_to_point[d] = {"date": d, "total_walks": 0, "total_distance_km": 0.0, "total_duration_min": 0}
        for row in daily:
            # row['date'] is UTC date; we want KST date; recompute by converting a noon UTC? assume boundaries handled via filter; keep iso date
            if row["date"] in date_to_point:
                date_to_point[row["date"]]["total_walks"] = row["total_walks"]
                date_to_point[row["date"]]["total_distance_km"] = row["total_distance_km"]
                date_to_point[row["date"]]["total_duration_min"] = row["total_duration_min"]

        points = list(date_to_point.values())

        total_walks = sum(p["total_walks"] for p in points)
        total_distance_km = round(sum(p["total_distance_km"] for p in points), 2)
        total_duration_min = sum(p["total_duration_min"] for p in points)
        active_days = sum(1 for p in points if p["total_walks"] > 0)
        total_days = len(points)

        avg_walks_per_day = round(total_walks / total_days, 2) if total_days > 0 else 0.0
        avg_distance_km_per_day = round(total_distance_km / total_days, 2) if total_days > 0 else 0.0
        avg_duration_min_per_day = round(total_duration_min / total_days, 2) if total_days > 0 else 0.0

        # Goal / Recommendation
        goal = self.repo.get_goal(pet_id)
        rec = self.repo.get_recommendation(pet_id)

        goal_walks = goal.target_walks if goal else None
        goal_minutes = goal.target_minutes if goal else None
        goal_distance = float(goal.target_distance_km) if goal else None

        # distribute daily goals as given values (they are per-day targets)
        for p in points:
            p["goal_walks"] = goal_walks
            p["goal_minutes"] = goal_minutes
            p["goal_distance_km"] = goal_distance

        # achievement rates compared to daily targets
        def safe_rate(total_value: float, target_per_day: Optional[float]) -> Optional[float]:
            if target_per_day and total_days > 0 and target_per_day > 0:
                return round((total_value / (target_per_day * total_days)), 2)
            return None

        summary_goal = {
            "has_goal": True if goal else False,
            "target_walks_per_day": goal_walks if goal else None,
            "target_minutes_per_day": goal_minutes if goal else None,
            "target_distance_km_per_day": goal_distance if goal else None,
            "achievement_rate_walks": safe_rate(total_walks, goal_walks) if goal else None,
            "achievement_rate_minutes": safe_rate(total_duration_min, goal_minutes) if goal else None,
            "achievement_rate_distance": safe_rate(total_distance_km, goal_distance) if goal else None,
        }

        summary_rec = {
            "has_recommendation": True if rec else False,
            "recommended_walks_per_day": rec.recommended_walks if rec else None,
            "recommended_minutes_per_day": rec.recommended_minutes if rec else None,
            "recommended_distance_km_per_day": float(rec.recommended_distance_km) if rec else None,
        }

        response_content = {
            "success": True,
            "status": 200,
            "period": period,
            "range": {"start_date": start_str, "end_date": end_str},
            "summary": {
                "pet_id": pet_id,
                "total_walks": total_walks,
                "total_distance_km": total_distance_km,
                "total_duration_min": total_duration_min,
                "active_days": active_days,
                "total_days": total_days,
                "avg_walks_per_day": avg_walks_per_day,
                "avg_distance_km_per_day": avg_distance_km_per_day,
                "avg_duration_min_per_day": avg_duration_min_per_day,
                "goal": summary_goal,
                "recommendation": summary_rec,
            },
            "chart": {
                "granularity": "daily",
                "points": points,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }

        return JSONResponse(status_code=200, content=jsonable_encoder(response_content))
