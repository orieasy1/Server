# app/domains/pets/service/my_pets_service.py

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.domains.pets.repository.pet_repository import PetRepository
from app.domains.auth.repository.auth_repository import AuthRepository


class MyPetsService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)

    def list_my_pets(
        self,
        request: Request,
        authorization: Optional[str],
    ):
        path = request.url.path

        # ------------------------
        # 1) Auth
        # ------------------------
        if authorization is None:
            return error_response(401, "MY_PETS_401_1", "Authorization 헤더가 필요합니다.", path)

        if not authorization.startswith("Bearer "):
            return error_response(401, "MY_PETS_401_2",
                                  "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "MY_PETS_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)

        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "MY_PETS_401_2",
                                  "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        firebase_uid = decoded.get("uid")

        # ------------------------
        # 2) User 조회
        # ------------------------
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            # 탈퇴 후 재로그인 등으로 DB에 유저가 없을 때 자동 생성
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
                auth_repo = AuthRepository(self.db)
                user = auth_repo.create_user(
                    firebase_uid=firebase_uid,
                    nickname=nickname,
                    email=email,
                    profile_img_url=picture,
                    sns=sns,
                )
            except Exception as e:
                print("MY_PETS_CREATE_USER_ERROR:", e)
                self.db.rollback()
                return error_response(500, "MY_PETS_500_2", "사용자 정보를 생성하는 중 오류가 발생했습니다.", path)

        # ------------------------
        # 3) Pet 조회
        # ------------------------
        try:
            rows = self.pet_repo.get_pets_for_user(user.user_id)
        except Exception as e:
            print("MY_PETS_QUERY_ERROR:", e)
            return error_response(500, "MY_PETS_500_1",
                                  "반려동물 목록을 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", path)

        # ------------------------
        # 4) 데이터 변환
        # ------------------------
        pets = []
        for pet, family in rows:
            pets.append({
                "pet_id": pet.pet_id,
                "family_id": pet.family_id,
                "family_name": family.family_name if family else None,
                "owner_id": pet.owner_id,
                "is_owner": (pet.owner_id == user.user_id),
                "pet_search_id": pet.pet_search_id,
                "name": pet.name,
                "breed": pet.breed,
                "age": pet.age,
                "weight": pet.weight,
                "gender": pet.gender.value if pet.gender else None,
                "image_url": pet.image_url,
                "disease": getattr(pet, 'disease', None),
                "voice_url": getattr(pet, 'voice_url', None),
                "created_at": pet.created_at.isoformat() if pet.created_at else None,
                "updated_at": pet.updated_at.isoformat() if pet.updated_at else None,
            })

        # ------------------------
        # 5) 성공 응답
        # ------------------------
        resp = {
            "success": True,
            "status": 200,
            "pets": pets,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }
        return JSONResponse(status_code=200, content=jsonable_encoder(resp))
