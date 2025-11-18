import re
from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.domains.users.repository.user_repository import UserRepository
from app.schemas.users.user_update_schema import UserUpdateRequest

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

        # 2) Firebase 토큰 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(401, "USER_GET_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 3) DB 조회
        repo = UserRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        if user is None:
            return error_response(404, "USER_GET_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 4) 정상 응답
        return {
            "success": True,
            "status": 200,
            "user": {
                "user_id": user.user_id,
                "firebase_uid": user.firebase_uid,
                "nickname": user.nickname,
                "email": user.email,
                "phone": user.phone,
                "profile_img_url": user.profile_img_url,
                "sns": user.sns, 
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        }

    @staticmethod
    def update_me(
        request: Request,
        authorization: Optional[str],
        body: UserUpdateRequest,
        db: Session,
    ):
        path = request.url.path

        # 1) Authorization 헤더 검사
        if authorization is None:
            return error_response(401, "USER_EDIT_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "USER_EDIT_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "USER_EDIT_401_3", "Authorization 헤더 형식이 잘못되었습니다.", path)

        id_token = parts[1]

        # 2) Firebase Token 검증
        decoded = verify_firebase_token(id_token)
        if decoded is None:
            return error_response(401, "USER_EDIT_401_4", "유효하지 않거나 만료된 Firebase ID Token입니다.", path)

        firebase_uid = decoded.get("uid")

        # 3) DB에서 유저 조회
        repo = UserRepository(db)
        user = repo.get_user_by_firebase_uid(firebase_uid)

        if user is None:
            return error_response(404, "USER_EDIT_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # 4) Body validation
        if not body or (body.nickname is None and body.phone is None):
            return error_response(400, "USER_EDIT_400_1", "수정할 필드가 존재하지 않습니다.", path)

        # 전화번호 검증
        if body.phone is not None:
            if not re.match(r"^010-\d{4}-\d{4}$", body.phone):
                return error_response(400, "USER_EDIT_400_3", "전화번호 형식이 올바르지 않습니다.", path)

        # 5) DB Update
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

        # 6) 성공 응답
        return {
            "success": True,
            "status": 200,
            "user": {
                "user_id": updated_user.user_id,
                "firebase_uid": updated_user.firebase_uid,
                "nickname": updated_user.nickname,
                "email": updated_user.email,
                "phone": updated_user.phone,
                "profile_img_url": updated_user.profile_img_url,
                "sns": updated_user.sns,
                "created_at": updated_user.created_at.isoformat(),
                "updated_at": updated_user.updated_at.isoformat() if updated_user.updated_at else None,
            }
        }
