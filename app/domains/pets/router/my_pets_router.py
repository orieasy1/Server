from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.schemas.error_schema import ErrorResponse
from app.schemas.pets.my_pets_schema import MyPetsResponse
from app.schemas.pets.pet_update_schema import PetUpdateRequest

from app.domains.pets.service.my_pets_service import MyPetsService
from app.domains.pets.service.pet_modify_service import PetModifyService


router = APIRouter(
    prefix="/api/v1/pets",
    tags=["Pets"]
)


# -------------------------------------------------------
# 1) 내가 속한 모든 family의 반려동물 목록 조회
# -------------------------------------------------------
@router.get(
    "/my",
    summary="내가 속한 모든 family의 반려동물 목록 조회",
    status_code=200,
    response_model=MyPetsResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def list_my_pets(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    service = MyPetsService(db)
    return service.list_my_pets(
        request=request,
        authorization=authorization,
    )
