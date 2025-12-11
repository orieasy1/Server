# app/domains/walk/service/ranking_service.py

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from app.core.firebase import verify_firebase_token
from app.domains.walk.exception import walk_error

from app.models.user import User
from app.models.family_member import FamilyMember

from app.domains.walk.repository.ranking_repository import RankingRepository


class RankingService:
    def __init__(self, db):
        self.db = db
        self.repo = RankingRepository(db)

    def get_ranking(self, request, authorization, family_id, period, pet_id):
        path = request.url.path

        # -------------------------
        # 1) Authorization
        # -------------------------
        if authorization is None:
            return walk_error("WALK_RANKING_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_RANKING_401_2", path)

        decoded = verify_firebase_token(authorization.split(" ")[1])
        if decoded is None:
            return walk_error("WALK_RANKING_401_2", path)

        # -------------------------
        # 2) 유저 조회
        # -------------------------
        firebase_uid = decoded.get("uid")
        user = self.db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not user:
            return walk_error("WALK_RANKING_401_3", path)

        # -------------------------
        # 3) family_id 유효성
        # -------------------------
        if family_id is None:
            return walk_error("WALK_RANKING_400_2", path)

        if not self.repo.check_family_exists(family_id):
            return walk_error("WALK_RANKING_404_1", path)

        # -------------------------
        # 4) 요청자가 family 구성원인지 확인
        # -------------------------
        member = (
            self.db.query(FamilyMember)
            .filter(FamilyMember.family_id == family_id)
            .filter(FamilyMember.user_id == user.user_id)
            .first()
        )
        if not member:
            return walk_error("WALK_RANKING_403_1", path)

        # -------------------------
        # 5) 기간 계산
        # -------------------------
        now = datetime.utcnow()

        if period == "weekly":
            start_dt = now - timedelta(days=now.weekday())
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=7)

        elif period == "monthly":
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (
                start_dt.replace(month=start_dt.month + 1)
                if start_dt.month < 12
                else start_dt.replace(year=start_dt.year + 1, month=1)
            )
            end_dt = next_month

        elif period == "total":
            start_dt = datetime(2000, 1, 1)
            end_dt = datetime(3000, 1, 1)

        else:
            return walk_error("WALK_RANKING_400_1", path)

        # -------------------------
        # 6) family 구성원 user_id 리스트
        # -------------------------
        user_ids = [row[0] for row in self.repo.get_family_members(family_id)]

        # -------------------------
        # 7) 집계
        # -------------------------
        stats = self.repo.get_walk_stats(user_ids, start_dt, end_dt, pet_id)

        # 🔥 추가된 부분 — 스펙 404-2 반영
        if not stats:
            return walk_error("WALK_RANKING_404_2", path)

        # -------------------------
        # 8) 랭킹 결과 생성
        # -------------------------
        ranking_items = []

        for idx, row in enumerate(stats, start=1):
            uid = row[0]
            usr = self.db.query(User).get(uid)

            pets = self.repo.get_user_pets(uid, start_dt, end_dt)

            ranking_items.append({
                "rank": idx,
                "user_id": uid,
                "nickname": usr.nickname,
                "profile_img_url": usr.profile_img_url,
                "total_distance_km": float(row.total_distance_km),
                "total_duration_min": int(row.total_duration_min),
                "walk_count": int(row.walk_count),
                "pets": [
                    {
                        "pet_id": p.pet_id,
                        "name": p.name,
                        "image_url": p.image_url
                    }
                    for p in pets
                ],
                "is_myself": (uid == user.user_id),
            })

        # -------------------------
        # 9) 최종 응답
        # -------------------------
        response = {
            "success": True,
            "status": 200,
            "family_id": family_id,
            "period": period,
            "ranking": ranking_items,
            "total_count": len(ranking_items),
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }

        return JSONResponse(status_code=200, content=jsonable_encoder(response))
