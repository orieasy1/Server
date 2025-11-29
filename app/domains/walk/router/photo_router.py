from fastapi import APIRouter, Header, Request, Depends, UploadFile, File, Form, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.photo_service import PhotoService
from app.schemas.error_schema import ErrorResponse
from app.schemas.walk.photo_schema import PhotoUploadResponse


router = APIRouter(
    prefix="/api/v1/walk",
    tags=["Walk"]
)


@router.post(
    "/sessions/{walk_id}/photo",
    summary="산책 사진 업로드",
    description="산책 종료 후 인증 사진을 업로드합니다. 종료된 산책에만 업로드 가능합니다.",
    status_code=201,
    response_model=PhotoUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (파일 형식/크기 오류 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "산책을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "진행 중인 산책에는 업로드 불가"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def upload_walk_photo(
    request: Request,
    walk_id: int = Path(..., description="산책 세션 ID"),
    file: UploadFile = File(..., description="이미지 파일 (JPG, PNG, 최대 10MB)"),
    caption: Optional[str] = Form(None, description="사진 설명"),
    photo_timestamp: Optional[str] = Form(None, description="사진 촬영 시간 (ISO 형식)"),
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 종료 후 인증 사진을 업로드합니다.
    
    - walk_id: 산책 세션 ID (path parameter)
    - file: 이미지 파일 (multipart/form-data, 필수)
    - caption: 사진 설명 (선택)
    - photo_timestamp: 사진 촬영 시간 (선택, 산책 시간 검증용)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 업로드 가능
    - 종료된 산책에만 업로드 가능
    - 파일 형식: JPG, PNG
    - 파일 크기: 최대 10MB
    """
    service = PhotoService(db)
    return service.upload_photo(
        request=request,
        authorization=authorization,
        walk_id=walk_id,
        file=file,
        caption=caption,
        photo_timestamp=photo_timestamp,
    )

