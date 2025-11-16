from fastapi import Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.firebase import verify_firebase_token, upload_file_to_storage
from app.core.error_handler import error_response
from app.models.user import User
from app.models.pet import Pet
from app.domains.pets.repository.pet_repository import PetRepository
from app.models.family_member import FamilyMember, MemberRole

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {".jpg", ".jpeg", ".png"}
ALLOWED_CT = {"image/jpeg", "image/jpg", "image/png"}


class PetImageService:
    def __init__(self, db: Session):
        self.db = db
        self.pet_repo = PetRepository(db)

    def upload_image(
        self,
        request: Request,
        authorization: Optional[str],
        pet_id: int,
        file: Optional[UploadFile],
    ):
        path = request.url.path

        # Auth
        if authorization is None:
            return error_response(401, "PET_IMG_401_1", "Authorization 헤더가 필요합니다.", path)
        if not authorization.startswith("Bearer "):
            return error_response(401, "PET_IMG_401_2", "Authorization 헤더는 'Bearer <token>' 형식이어야 합니다.", path)
        parts = authorization.split(" ")
        if len(parts) != 2:
            return error_response(401, "PET_IMG_401_2", "Authorization 헤더 형식이 잘못되었습니다.", path)
        decoded = verify_firebase_token(parts[1])
        if decoded is None:
            return error_response(401, "PET_IMG_401_2", "유효하지 않거나 만료된 Firebase ID Token입니다. 다시 로그인해주세요.", path)

        # User
        firebase_uid = decoded.get("uid")
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )
        if not user:
            return error_response(404, "PET_IMG_404_1", "해당 사용자를 찾을 수 없습니다.", path)

        # Pet
        pet: Optional[Pet] = self.pet_repo.get_by_id(pet_id)
        if not pet:
            return error_response(404, "PET_IMG_404_2", "요청하신 반려동물을 찾을 수 없습니다.", path)

        # Owner check
        if not (pet.owner_id == user.user_id or self._is_owner_member(user.user_id, pet)):
            return error_response(403, "PET_IMG_403_1", "해당 반려동물의 이미지를 수정할 권한이 없습니다.", path)

        # Validate file
        if file is None:
            return error_response(400, "PET_IMG_400_1", "업로드할 이미지 파일이 필요합니다.", path)

        filename = (file.filename or "").strip()
        lower = filename.lower()
        import os
        ext = os.path.splitext(lower)[1]
        if ext not in ALLOWED_EXT:
            return error_response(400, "PET_IMG_400_2", "지원하지 않는 이미지 형식입니다. JPG 또는 PNG 파일을 업로드해주세요.", path)

        content_type = file.content_type or ""
        if content_type.lower() not in ALLOWED_CT:
            return error_response(400, "PET_IMG_400_2", "지원하지 않는 이미지 형식입니다. JPG 또는 PNG 파일을 업로드해주세요.", path)

        try:
            content = await file.read()  # type: ignore
        except Exception:
            return error_response(500, "PET_IMG_500_3", "반려동물 이미지를 변경하는 중 알 수 없는 서버 오류가 발생했습니다.", path)
        if not content:
            return error_response(400, "PET_IMG_400_1", "업로드할 이미지 파일이 필요합니다.", path)
        if len(content) > MAX_IMAGE_BYTES:
            return error_response(400, "PET_IMG_400_3", "이미지 파일 크기가 허용 범위를 초과했습니다.", path)

        # Upload to Firebase Storage
        try:
            url = upload_file_to_storage(
                file_content=content,
                file_name=filename,
                content_type=content_type,
                folder="pet_profiles",
            )
        except Exception:
            return error_response(500, "PET_IMG_500_1", "이미지 업로드 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", path)

        # Update DB
        try:
            pet.image_url = url
            self.db.flush()
            self.db.commit()
            self.db.refresh(pet)
        except Exception:
            self.db.rollback()
            return error_response(500, "PET_IMG_500_2", "반려동물 이미지 URL을 저장하는 중 오류가 발생했습니다.", path)

        resp = {
            "success": True,
            "status": 200,
            "image_url": url,
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path,
        }
        return JSONResponse(status_code=200, content=jsonable_encoder(resp))

    def _is_owner_member(self, user_id: int, pet: Pet) -> bool:
        fm = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user_id,
                FamilyMember.role == MemberRole.OWNER,
            )
            .first()
        )
        return fm is not None
