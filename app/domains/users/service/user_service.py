import re
from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.domains.users.repository.user_repository import UserRepository
from app.domains.auth.repository.auth_repository import AuthRepository

from app.schemas.users.user_base_schema import UserBase
from app.schemas.users.user_update_schema import UserUpdateRequest
from app.schemas.users.user_response_schema import UserMeResponse


class UserService:

    @staticmethod
    def get_me(request: Request, authorization: Optional[str], db: Session):

        path = request.url.path

        # 1) Authorization 헤더 확인
        if authorization is None:
            return error_response(401, "USER_GET_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "USER_GET_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "USER_GET_401_3", "Authorization 헤더 형식이 잘못되었습니다.", path)

        id_token = parts[1]

        # 2) Firebase Token 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(401, "USER_GET_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 3) DB 조회
        repo = UserRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        if user is None:
            # 탈퇴 후 재로그인 등으로 DB에 유저가 없을 경우 자동 생성
            try:
                provider = decoded.get("firebase", {}).get("sign_in_provider")
                provider_map = {
                    "google.com": "google",
                    "apple.com": "apple",
                    "oidc.kakao": "kakao",
                    "custom": "kakao",
                    "password": "email",
                }
                sns = provider_map.get(provider, "email")
                nickname = decoded.get("name") or decoded.get("displayName") or f"user_{firebase_uid[:6]}"
                email = decoded.get("email")
                picture = decoded.get("picture")
                auth_repo = AuthRepository(db)
                user = auth_repo.create_user(
                    firebase_uid=firebase_uid,
                    nickname=nickname,
                    email=email,
                    profile_img_url=picture,
                    sns=sns,
                )
            except Exception as e:
                print("USER_GET_CREATE_ERROR:", e)
                db.rollback()
                return error_response(500, "USER_GET_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다.", path)

        # 4) Pydantic 스키마 변환
        user_schema = UserBase(
            user_id=user.user_id,
            firebase_uid=user.firebase_uid,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            profile_img_url=user.profile_img_url,
            sns=user.sns,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat() if user.updated_at else None
        )

        return UserMeResponse(
            success=True,
            status=200,
            user=user_schema
        )


    @staticmethod
    def update_me(
        request: Request,
        authorization: Optional[str],
        body: UserUpdateRequest,
        db: Session,
    ):
        path = request.url.path

        # 1) Authorization 헤더 확인
        if authorization is None:
            return error_response(401, "USER_EDIT_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "USER_EDIT_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "USER_EDIT_401_3", "Authorization 헤더 형식이 잘못되었습니다.", path)

        id_token = parts[1]

        # 2) Firebase 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(401, "USER_EDIT_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 3) DB user 조회
        repo = UserRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        if user is None:
            # 사용자 없으면 자동 생성
            try:
                provider = decoded.get("firebase", {}).get("sign_in_provider")
                provider_map = {
                    "google.com": "google",
                    "apple.com": "apple",
                    "oidc.kakao": "kakao",
                    "custom": "kakao",
                    "password": "email",
                }
                sns = provider_map.get(provider, "email")
                nickname = decoded.get("name") or decoded.get("displayName") or f"user_{firebase_uid[:6]}"
                email = decoded.get("email")
                picture = decoded.get("picture")
                auth_repo = AuthRepository(db)
                user = auth_repo.create_user(
                    firebase_uid=firebase_uid,
                    nickname=nickname,
                    email=email,
                    profile_img_url=picture,
                    sns=sns,
                )
            except Exception as e:
                print("USER_EDIT_CREATE_ERROR:", e)
                db.rollback()
                return error_response(500, "USER_EDIT_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다.", path)

        # 4) Body 검증
        if not body or (body.nickname is None and body.phone is None):
            return error_response(400, "USER_EDIT_400_1", "수정할 필드가 존재하지 않습니다.", path)

        # 전화번호 형식 검증
        if body.phone is not None:
            if not re.match(r"^010-\d{4}-\d{4}$", body.phone):
                return error_response(400, "USER_EDIT_400_3", "전화번호 형식이 올바르지 않습니다.", path)

        # 5) 수정 처리
        try:
            updated_user = repo.update_user(
                user,
                nickname=body.nickname,
                phone=body.phone
            )
        except Exception as e:
            print("USER_UPDATE_ERROR:", e)
            db.rollback()
            return error_response(500, "USER_EDIT_500_1", "사용자 정보를 수정하는 중 오류가 발생했습니다.", path)

        # 6) 응답 스키마 변환
        updated_schema = UserBase(
            user_id=updated_user.user_id,
            firebase_uid=updated_user.firebase_uid,
            nickname=updated_user.nickname,
            email=updated_user.email,
            phone=updated_user.phone,
            profile_img_url=updated_user.profile_img_url,
            sns=updated_user.sns,
            created_at=updated_user.created_at.isoformat(),
            updated_at=updated_user.updated_at.isoformat() if updated_user.updated_at else None
        )

        return UserMeResponse(
            success=True,
            status=200,
            user=updated_schema
        )

    @staticmethod
    def update_fcm_token(
        request: Request,
        authorization: Optional[str],
        fcm_token: str,
        db: Session,
    ):
        """FCM 푸시 알림 토큰을 업데이트합니다."""
        path = request.url.path

        # 1) Authorization 헤더 확인
        if authorization is None:
            return error_response(401, "FCM_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "FCM_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "FCM_401_3", "Authorization 헤더 형식이 잘못되었습니다.", path)

        id_token = parts[1]

        # 2) Firebase 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(401, "FCM_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 3) DB user 조회
        repo = UserRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        if user is None:
            # 사용자 없으면 자동 생성
            try:
                provider = decoded.get("firebase", {}).get("sign_in_provider")
                provider_map = {
                    "google.com": "google",
                    "apple.com": "apple",
                    "oidc.kakao": "kakao",
                    "custom": "kakao",
                    "password": "email",
                }
                sns = provider_map.get(provider, "email")
                nickname = decoded.get("name") or decoded.get("displayName") or f"user_{firebase_uid[:6]}"
                email = decoded.get("email")
                picture = decoded.get("picture")
                auth_repo = AuthRepository(db)
                user = auth_repo.create_user(
                    firebase_uid=firebase_uid,
                    nickname=nickname,
                    email=email,
                    profile_img_url=picture,
                    sns=sns,
                )
            except Exception as e:
                print("FCM_CREATE_ERROR:", e)
                db.rollback()
                return error_response(500, "FCM_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다.", path)

        # 4) FCM 토큰 업데이트
        try:
            user.fcm_token = fcm_token
            db.commit()
            db.refresh(user)
            print(f"[INFO] FCM token updated for user {user.user_id}: {fcm_token[:20]}...")
        except Exception as e:
            print(f"[ERROR] FCM token update failed: {e}")
            db.rollback()
            return error_response(500, "FCM_500_1", "FCM 토큰 업데이트 중 오류가 발생했습니다.", path)

        return {
            "success": True,
            "status": 200,
            "message": "FCM 토큰이 성공적으로 업데이트되었습니다."
        }