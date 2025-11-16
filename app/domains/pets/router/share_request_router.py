from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.schemas.error_schema import ErrorResponse
from app.schemas.pets.pet_share_request_schema import (
    PetShareRequestResponse,
    PetShareRequestCreate,
    PetShareApproveRequest,
    PetShareApproveResponse,
)
from app.domains.pets.service.share_request_service import PetShareRequestService

router = APIRouter(
    prefix="/api/v1/pets",
    tags=["Pets"]
)


@router.post(
    "/{pet_search_id}/request",
    summary="반려동물 초대코드로 공유 요청 생성",
    status_code=201,
    response_model=PetShareRequestResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_pet_share_request(
    pet_search_id: str,
    request: Request,
    body: PetShareRequestCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = PetShareRequestService(db)
    return service.create_request(
        request=request,
        authorization=authorization,
        pet_search_id=pet_search_id,
        body=body,
    )


@router.patch(
    "/share/{request_id}",
    summary="반려동물 공유 요청 승인/거절",
    status_code=200,
    response_model=PetShareApproveResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def approve_pet_share_request(
    request: Request,
    request_id: int,
    body: PetShareApproveRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = PetShareRequestService(db)
    return service.approve_request(
        request=request,
        authorization=authorization,
        request_id=request_id,
        body=body,
    )
