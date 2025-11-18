from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db

from app.schemas.error_schema import ErrorResponse
from app.schemas.pets.pet_register_schema import PetRegisterRequest
from app.schemas.pets.pet_update_schema import PetUpdateRequest, PetUpdateResponse
from app.schemas.pets.pet_image_schema import PetImageResponse

from app.domains.pets.service.register_service import PetRegisterService
from app.domains.pets.service.pet_modify_service import PetModifyService

router = APIRouter(
    prefix="/api/v1/pets",
    tags=["Pets"]
)

# ------------------------
# 1. 반려동물 등록
# ------------------------
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
    return service.register_pet(request, authorization, body)

# ------------------------
# 2. 반려동물 정보 부분 수정
# ------------------------
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
    service = PetModifyService(db)
    return service.update_pet_detail(request, authorization, pet_id, body)

# ------------------------
# 3. 반려동물 이미지 URL 업데이트
# ------------------------
@router.post(
    "/{pet_id}/image",
    summary="반려동물 이미지 URL 업데이트",
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
def update_pet_image(
    pet_id: int,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = PetModifyService(db)
    return service.update_pet_image(request, authorization, pet_id, body.image_url)
