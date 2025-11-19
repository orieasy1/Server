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
    description="현재 사용자가 속한 모든 가족 그룹의 반려동물 목록을 조회합니다.",
    status_code=200,
    response_model=MyPetsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def list_my_pets(
    request: Request,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    내가 속한 모든 가족 그룹의 반려동물 목록을 조회합니다.
    
    - 현재 사용자가 owner이거나 member로 속한 모든 반려동물 반환
    - 각 반려동물의 소유자 여부(is_owner) 정보 포함
    - 가족 그룹별로 구분되어 반환
    """
    service = MyPetsService(db)
    return service.list_my_pets(
        request=request,
        authorization=authorization,
    )
