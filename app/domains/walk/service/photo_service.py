from fastapi import Request, UploadFile, File, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os

from app.core.firebase import verify_firebase_token, upload_file_to_storage
from app.domains.walk.exception import walk_error
from app.models.user import User
from app.models.pet import Pet
from app.models.family_member import FamilyMember
from app.domains.walk.repository.photo_repository import PhotoRepository
from app.domains.walk.repository.session_repository import SessionRepository

# 파일 크기 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class PhotoService:
    def __init__(self, db: Session):
        self.db = db
        self.photo_repo = PhotoRepository(db)
        self.session_repo = SessionRepository(db)

    def upload_photo(
        self,
        request: Request,
        authorization: Optional[str],
        walk_id: int,
        file: UploadFile = File(...),
        caption: Optional[str] = Form(None),
        photo_timestamp: Optional[str] = Form(None),
    ):
        path = request.url.path

        # ============================================
        # 1) Authorization 검증
        # ============================================
        if authorization is None:
            return walk_error("WALK_PHOTO_401_1", path)

        if not authorization.startswith("Bearer "):
            return walk_error("WALK_PHOTO_401_2", path)

        parts = authorization.split(" ")
        if len(parts) != 2:
            return walk_error("WALK_PHOTO_401_2", path)

        id_token = parts[1]
        decoded = verify_firebase_token(id_token)

        if decoded is None:
            return walk_error("WALK_PHOTO_401_2", path)

        firebase_uid = decoded.get("uid")

        # ============================================
        # 2) 사용자 조회
        # ============================================
        user: User = (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            return walk_error("WALK_PHOTO_404_1", path)

        # ============================================
        # 3) 파일 유효성 검사
        # ============================================
        # 3-1) 파일 존재 체크
        if not file or not file.filename:
            return walk_error("WALK_PHOTO_400_1", path)

        # 3-2) 파일 확장자 체크
        file_extension = None
        if file.filename:
            file_extension = os.path.splitext(file.filename.lower())[1]
            if file_extension not in ALLOWED_EXTENSIONS:
                return walk_error("WALK_PHOTO_400_2", path)

        # 3-3) 파일 크기 체크
        try:
            file_content = file.file.read()
            file_size = len(file_content)
            
            if file_size > MAX_FILE_SIZE:
                return walk_error("WALK_PHOTO_400_3", path)
            
            if file_size == 0:
                return walk_error("WALK_PHOTO_400_1", path)
        except Exception as e:
            print("FILE_READ_ERROR:", e)
            return walk_error("WALK_PHOTO_400_1", path)

        # ============================================
        # 4) 산책 세션 조회
        # ============================================
        try:
            walk = self.session_repo.get_walk_by_walk_id(walk_id)
            
            if not walk:
                return walk_error("WALK_PHOTO_404_2", path)
        except Exception as e:
            print("WALK_QUERY_ERROR:", e)
            return walk_error("WALK_PHOTO_500_2", path)

        # ============================================
        # 5) 산책 종료 여부 체크
        # ============================================
        if walk.end_time is None:
            return walk_error("WALK_PHOTO_409_1", path)

        # ============================================
        # 6) 권한 체크 (family_members 확인)
        # ============================================
        pet: Pet = (
            self.db.query(Pet)
            .filter(Pet.pet_id == walk.pet_id)
            .first()
        )

        if not pet:
            return walk_error("WALK_PHOTO_404_2", path)

        family_member: FamilyMember = (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.user_id
            )
            .first()
        )

        if not family_member:
            return walk_error("WALK_PHOTO_403_1", path)

        # ============================================
        # 7) 사진 촬영 시간 검증 (선택)
        # ============================================
        if photo_timestamp:
            try:
                photo_time = datetime.fromisoformat(photo_timestamp.replace('Z', '+00:00'))
                walk_start = walk.start_time
                walk_end = walk.end_time
                
                # UTC로 변환하여 비교
                if walk_start and walk_end:
                    if photo_time < walk_start or photo_time > walk_end:
                        return walk_error("WALK_PHOTO_400_4", path)
            except (ValueError, AttributeError):
                # timestamp 파싱 실패는 무시 (선택 필드이므로)
                pass

        # ============================================
        # 8) Firebase Storage 업로드
        # ============================================
        try:
            # 파일명 생성
            file_name = f"walk_{walk_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            
            # Content-Type 결정
            content_type = "image/jpeg" if file_extension in [".jpg", ".jpeg"] else "image/png"
            
            # Firebase Storage 업로드
            image_url = upload_file_to_storage(
                file_content=file_content,
                file_name=file_name,
                content_type=content_type,
                folder="walk_photos"
            )
        except Exception as e:
            print("STORAGE_UPLOAD_ERROR:", e)
            return walk_error("WALK_PHOTO_500_1", path)

        # ============================================
        # 9) DB에 사진 정보 저장
        # ============================================
        try:
            photo = self.photo_repo.create_photo(
                walk_id=walk_id,
                image_url=image_url,
                uploaded_by=user.user_id,
                caption=caption,
            )
            
            self.db.commit()
            self.db.refresh(photo)

        except Exception as e:
            print("PHOTO_SAVE_ERROR:", e)
            self.db.rollback()
            # Storage에 업로드된 파일은 나중에 정리 작업으로 삭제 가능
            return walk_error("WALK_PHOTO_500_2", path)

        # ============================================
        # 10) 응답 생성
        # ============================================
        response_content = {
            "success": True,
            "status": 201,
            "photo": {
                "photo_id": photo.photo_id,
                "walk_id": photo.walk_id,
                "image_url": photo.image_url,
                "uploaded_by": photo.uploaded_by,
                "caption": photo.caption,
                "created_at": photo.created_at.isoformat() if photo.created_at else None,
            },
            "timeStamp": datetime.utcnow().isoformat(),
            "path": path
        }

        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=201, content=encoded)

