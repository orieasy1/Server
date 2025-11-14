from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.domains.auth.repository.auth_repository import AuthRepository


class AuthService:

    @staticmethod
    def login(request: Request, authorization: Optional[str], db: Session):

        # 1) Authorization 헤더 확인
        if authorization is None:
            return error_response(
                401, "AUTH_401_1", "Authorization 헤더가 필요합니다.", request.url.path
            )

        if not authorization.startswith("Bearer "):
            return error_response(
                401, "AUTH_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", request.url.path
            )

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(
                401, "AUTH_401_3", "Authorization 헤더 형식이 잘못되었습니다.", request.url.path
            )

        id_token = parts[1]

        # 2) Firebase 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(
                401, "AUTH_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", request.url.path
            )

        firebase_uid = decoded.get("uid")
        email = decoded.get("email")
        nickname = decoded.get("name") or decoded.get("displayName")
        picture = decoded.get("picture")
        provider = decoded.get("firebase", {}).get("sign_in_provider")

        # 3) 필수 필드 확인
        if not firebase_uid:
            return error_response(
                400, "AUTH_400_1", "Firebase UID를 토큰에서 찾을 수 없습니다.", request.url.path
            )

        if not provider:
            return error_response(
                400, "AUTH_400_2", "Firebase 인증 제공자 정보를 확인할 수 없습니다.", request.url.path
            )

        # 4) DB 접근
        repo = AuthRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        if user:
            return {
                "is_new_user": False,
                "user": {
                    "user_id": user.user_id,
                    "firebase_uid": user.firebase_uid,
                    "nickname": user.nickname,
                    "email": user.email,
                    "phone": user.phone,
                    "profile_img_url": user.profile_img_url,
                    "provider": provider
                }
            }

        # 5) 신규 회원가입
        try:
            new_user = repo.create_user(
                firebase_uid=firebase_uid,
                nickname=nickname or f"user_{firebase_uid[:6]}",
                email=email,
                picture=picture
            )
        except:
            return error_response(
                500, "AUTH_500_1", "데이터베이스 처리 중 오류가 발생했습니다.", request.url.path
            )

        # 6) 응답
        return {
            "is_new_user": True,
            "user": {
                "user_id": new_user.user_id,
                "firebase_uid": new_user.firebase_uid,
                "nickname": new_user.nickname,
                "email": new_user.email,
                "phone": new_user.phone,
                "profile_img_url": new_user.profile_img_url,
                "provider": provider
            }
        }
