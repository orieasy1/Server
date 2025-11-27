import json
from datetime import datetime
from fastapi.responses import JSONResponse
from openai import OpenAI

from app.core.config import settings
from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response

from app.models.user import User
from app.models.notification import NotificationType
from app.domains.notifications.repository.notification_repository import NotificationRepository
from app.domains.notifications.repository.health_repository import HealthRepository

from app.schemas.notifications.common_action_schema import (
    NotificationActionResponse,
    NotificationActionItem,
)


class HealthService:
    def __init__(self, db):
        self.db = db
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.health_repo = HealthRepository(db)
        self.notif_repo = NotificationRepository(db)

    # ============================================================
    # 🔥 GPT 건강 피드백 생성 (전반 건강 요약)
    # ============================================================
    def _generate_health_advice(self, pet, weekly_minutes, rec_info):
        prompt = f"""
        너는 전문 수의사이자 반려동물 건강 코치야.
        다음 정보를 분석하고 **전반적인 건강 요약 보고서**를 JSON으로 출력해줘.

        JSON 형식:
        {{
            "title": "string",
            "message": "string",
            "tags": ["a", "b"]
        }}

        --- 신체 정보 ---
        이름: {pet.name}
        견종: {pet.breed}
        나이: {pet.age}
        체중: {pet.weight}
        질병: {pet.disease}

        --- 활동 정보 ---
        최근 7일 산책 시간: {weekly_minutes}분
        추천 산책: 최소 {rec_info["min_minutes"]}, 적정 {rec_info["recommended_minutes"]}, 최대 {rec_info["max_minutes"]}

        message는 3~5문장, title은 한 문장.
        """

        try:
            gpt_res = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.5,
                messages=[
                    {"role": "system", "content": "Output JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )

            raw = gpt_res.choices[0].message.content.strip()
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            advice = json.loads(cleaned)

            # fallback
            if not isinstance(advice.get("title"), str):
                advice["title"] = "건강 피드백"
            if not isinstance(advice.get("message"), str):
                advice["message"] = "건강 요약 정보를 생성하는 중입니다."

            return advice

        except Exception as e:
            print("HEALTH GPT ERROR:", e)
            return None

    # ============================================================
    # 🔥 건강 피드백 API — 개인 알림 전용
    # ============================================================
    def generate_health_feedback(self, request, authorization, body):
        path = request.url.path

        # 인증
        if not authorization or not authorization.startswith("Bearer "):
            return error_response(401, "H401", "Authorization 필요", path)

        decoded = verify_firebase_token(authorization.split(" ")[1])
        if decoded is None:
            return error_response(401, "H401_2", "Invalid token", path)

        user = self.db.query(User).filter(User.firebase_uid == decoded["uid"]).first()
        if not user:
            return error_response(404, "H404_1", "사용자 없음", path)

        pet = self.health_repo.get_pet(body.pet_id)
        if not pet:
            return error_response(404, "H404_2", "반려동물 없음", path)

        if not self.health_repo.user_in_family(user.user_id, pet.family_id):
            return error_response(403, "H403", "권한 없음", path)

        weekly_minutes = self.health_repo.get_weekly_walk_minutes(pet.pet_id)
        rec = self.health_repo.get_recommendation(pet.pet_id)
        rec_info = {
            "min_minutes": rec.min_minutes if rec else None,
            "recommended_minutes": rec.recommended_minutes if rec else None,
            "max_minutes": rec.max_minutes if rec else None,
        }

        advice = self._generate_health_advice(pet, weekly_minutes, rec_info)
        if advice is None:
            return error_response(500, "H500", "LLM 오류", path)

        # 개인 알림 저장 (broadcast 없음)
        notif = self.notif_repo.create_notification(
            family_id=pet.family_id,
            target_user_id=user.user_id,   # ⭐ 개인 알림
            related_pet_id=pet.pet_id,
            related_user_id=user.user_id,
            notif_type=NotificationType.SYSTEM_HEALTH,
            title=advice["title"],
            message=advice["message"],
        )
        self.db.commit()

        # ============================================================
        # 🔥 공통 스키마 객체 생성하여 반환
        # ============================================================
        return NotificationActionResponse(
            success=True,
            status=200,
            notification=NotificationActionItem(
                notification_id=notif.notification_id,
                type="SYSTEM_HEALTH",
                title=notif.title,
                message=notif.message,
                family_id=pet.family_id,
                target_user_id=user.user_id,
                related_pet_id=pet.pet_id,
                related_user_id=user.user_id,
                created_at=notif.created_at,
            ),
            timeStamp=datetime.utcnow().isoformat(),
            path=path,
        )
