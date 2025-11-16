from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token
from app.core.error_handler import error_response
from app.models.user import User
from app.domains.pets.repository.my_pets_repository import MyPetsRepository


class MyPetsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MyPetsRepository(db)

    def list_my_pets(
        self,
        request: Request,
        authorization: Optional[str],
    ):
        path = request.url.path

        # Auth
        if authorization is None:
            return error_response(401, "MY_PETS_401_1", "Authorization 헤더가 필요합니다.", path)
        if not authorization.startswith("Bearer "):
            return error_response(401, "MY_PETS_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)
        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "MY_PETS_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)
        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "MY_PETS_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        # User
        firebase_uid = decoded.get("uid")
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "MY_PETS_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # Query pets via family memberships
        try:
            rows = self.repo.list_pets_for_user(user.user_id)
        except Exception as e:
            print("MY_PETS_QUERY_ERROR:", e)
            return error_response(500, "MY_PETS_500_1", "반려동물 목록을 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", path)

        items = []
        for pet, family, is_owner in rows:
            items.append({
                "pet_id": pet.pet_id,
                "family_id": pet.family_id,
                "family_name": family.family_name if family else None,
                "owner_id": pet.owner_id,
                "is_owner": bool(is_owner),
                "name": pet.name,
                "breed": pet.breed,
                "age": pet.age,
                "weight": pet.weight,
                "gender": pet.gender.value if hasattr(pet, 'gender') and pet.gender else None,
                "image_url": pet.image_url,
                "created_at": pet.created_at.isoformat() if pet.created_at else None,
                "updated_at": pet.updated_at.isoformat() if hasattr(pet, 'updated_at') and pet.updated_at else None,
            })

        resp = {
            "success": True,
            "status": 200,
            "pets": items,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }
        return JSONResponse(status_code=200, content=jsonable_encoder(resp))
