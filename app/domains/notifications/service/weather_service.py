import json
import requests
from datetime import datetime
import pytz

from fastapi.responses import JSONResponse
from openai import OpenAI

from app.core.config import settings
from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response

from app.models.user import User
from app.models.notification import NotificationType
from app.models.notification_reads import NotificationRead

from app.domains.notifications.repository.weather_repository import WeatherRepository
from app.domains.notifications.repository.notification_repository import NotificationRepository

from app.schemas.notifications.common_action_schema import (
    NotificationActionResponse,
    NotificationActionItem,
)

KST = pytz.timezone("Asia/Seoul")


class WeatherService:
    def __init__(self, db):
        self.db = db
        self.weather_repo = WeatherRepository(db)
        self.notif_repo = NotificationRepository(db)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # ------------------------------------------------------------
    # 1) 외부 날씨 API
    # ------------------------------------------------------------
    def fetch_weather(self, lat, lng):
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"lat={lat}&lon={lng}&appid={settings.OPENWEATHER_API_KEY}"
                f"&units=metric&lang=kr"
            )
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                print("WEATHER API ERROR:", res.text)
                return None

            d = res.json()
            return {
                "condition": d["weather"][0]["main"],
                "condition_ko": d["weather"][0]["description"],
                "temperature_c": d["main"]["temp"],
                "humidity": d["main"]["humidity"],
            }

        except Exception as e:
            print("WEATHER FETCH ERROR:", e)
            return None

    # ------------------------------------------------------------
    # 2) GPT
    # ------------------------------------------------------------
    def generate_advice(self, pet, weekly_minutes, rec_info, weather, trigger):
        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""
        너는 반려동물 산책 전문가야.
        다음 정보를 분석해 오늘 산책 추천을 JSON으로 출력해줘.

        JSON:
        {{
            "title": "string",
            "message": "string",
            "suggested_time_slots": [
                {{
                    "label": "string",
                    "start_time": "HH:MM",
                    "end_time": "HH:MM"
                }}
            ],
            "suggested_duration_min": 20,
            "notes": ["주의1", "주의2"]
        }}

        --- 날씨 ---
        상태: {weather["condition_ko"]}
        기온: {weather["temperature_c"]}℃
        습도: {weather["humidity"]}%

        --- 반려동물 ---
        이름: {pet.name}
        견종: {pet.breed}
        나이: {pet.age}
        체중: {pet.weight}
        질병: {pet.disease}

        최근 산책: {weekly_minutes}분
        """

        res = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": "Output JSON only."},
                {"role": "user", "content": prompt},
            ],
        )

        content = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        advice = json.loads(content)

        if not isinstance(advice.get("title"), str):
            advice["title"] = "산책 추천"
        if not isinstance(advice.get("message"), str):
            advice["message"] = "산책 추천 정보를 생성하는 중입니다."

        return advice

    # ------------------------------------------------------------
    # 3) 디테일 포함 message 생성
    # ------------------------------------------------------------
    def build_message(self, weather, advice):
        weather_text = f"오늘 날씨는 {weather['condition_ko']}({weather['temperature_c']}℃)입니다."
        slots = advice.get("suggested_time_slots", [])
        if slots:
            s = slots[0]
            time_text = f"추천 시간대: {s['start_time']}~{s['end_time']}"
        else:
            time_text = "추천 시간대를 찾기 어려움"

        notes = advice.get("notes", [])
        note_text = f"\n주의사항: {notes[0]}" if notes else ""

        return f"{advice['message']}\n\n{weather_text}\n{time_text}{note_text}"

    # ------------------------------------------------------------
    # 4) Weather 추천 — 개인 알림
    # ------------------------------------------------------------
    def generate_weather_recommendation(self, request, authorization, body):
        path = request.url.path

        # 인증
        if not authorization or not authorization.startswith("Bearer "):
            return error_response(401, "W401", "Authorization 필요", path)

        decoded = verify_firebase_token(authorization.split(" ")[1])
        if decoded is None:
            return error_response(401, "W401_2", "Invalid token", path)

        user = self.db.query(User).filter(User.firebase_uid == decoded["uid"]).first()
        if not user:
            return error_response(404, "W404_1", "사용자 없음", path)

        pet = self.weather_repo.get_pet(body.pet_id)
        if not pet:
            return error_response(404, "W404_2", "반려동물 없음", path)

        if not self.weather_repo.user_in_family(user.user_id, pet.family_id):
            return error_response(403, "W403", "권한 없음", path)

        weather = self.fetch_weather(body.lat, body.lng)
        if not weather:
            return error_response(502, "W502", "날씨 API 오류", path)

        weekly_minutes = self.weather_repo.get_weekly_walk_minutes(pet.pet_id)

        rec = self.weather_repo.get_recommendation(pet.pet_id)
        rec_info = {
            "min_minutes": rec.min_minutes if rec else None,
            "recommended_minutes": rec.recommended_minutes if rec else None,
            "max_minutes": rec.max_minutes if rec else None,
        }

        advice = self.generate_advice(pet, weekly_minutes, rec_info, weather, body.trigger_type)
        final_message = self.build_message(weather, advice)

        # 개인 알림 저장
        notif = self.notif_repo.create_notification(
            family_id=pet.family_id,
            target_user_id=user.user_id,
            related_pet_id=pet.pet_id,
            related_user_id=user.user_id,
            notif_type=NotificationType.SYSTEM_WEATHER,
            title=advice["title"],
            message=final_message,
        )
        self.db.commit()

        # 자동 읽음 처리
        read = NotificationRead(
            notification_id=notif.notification_id,
            user_id=user.user_id
        )
        self.db.add(read)
        self.db.commit()

        # ------------------------------------------------------------
        # ⭐ 공통 스키마 응답
        # ------------------------------------------------------------
        return NotificationActionResponse(
            success=True,
            status=200,
            notification=NotificationActionItem(
                notification_id=notif.notification_id,
                type="SYSTEM_WEATHER",
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
