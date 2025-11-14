from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.schemas.pets.pet_register_schema import PetRegisterRequest
from app.domains.pets.service.register_service import PetRegisterService
from app.schemas.error_schema import ErrorResponse   # 🔥 추가


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
