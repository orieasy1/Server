from fastapi import APIRouter, Header, Request, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.schemas.pets.pet_register_schema import PetRegisterRequest
from app.domains.pets.service.register_service import PetRegisterService
from app.schemas.error_schema import ErrorResponse   # 🔥 추가
from app.domains.pets.service.pet_update_service import PetUpdateService
from app.schemas.pets.pet_update_schema import PetUpdateRequest, PetUpdateResponse
from app.domains.pets.service.pet_image_service import PetImageService
from app.schemas.pets.pet_image_schema import PetImageResponse


router = APIRouter(
    prefix="/api/v1/pets",
    tags=["Pets"]
)


@router.post(
    "",
    summary="반려동물 신규 등록",
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def register_pet(
    request: Request,
    body: PetRegisterRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = PetRegisterService(db)
    return service.register_pet(
        request=request,
        authorization=authorization,
        body=body,
    )


@router.patch(
    "/{pet_id}",
    summary="반려동물 세부 정보 부분 수정",
    status_code=200,
    response_model=PetUpdateResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def update_pet(
    pet_id: int,
    request: Request,
    body: PetUpdateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = PetUpdateService(db)
    return service.patch_pet(
        request=request,
        authorization=authorization,
        pet_id=pet_id,
        body=body,
    )


@router.post(
    "/{pet_id}/image",
    summary="반려동물 프로필 이미지 업로드/변경",
    status_code=200,
    response_model=PetImageResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def upload_pet_image(
    pet_id: int,
    request: Request,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = PetImageService(db)
    return service.upload_image(
        request=request,
        authorization=authorization,
        pet_id=pet_id,
        file=file,
    )
