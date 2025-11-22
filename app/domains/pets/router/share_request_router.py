from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.schemas.error_schema import ErrorResponse
from app.schemas.pets.pet_share_request_schema import (
    PetShareRequestResponse,
    PetShareApproveRequest,
    PetShareApproveResponse,
    MyShareRequestListResponse
)
from app.domains.pets.service.share_request_service import PetShareRequestService

router = APIRouter(
    prefix="/api/v1/pets",
    tags=["Pets"]
)

# ---------------------------------------------------------
# 1) 공유 요청 생성 (body 없음)
# ---------------------------------------------------------
@router.post(
    "/{pet_search_id}/request",
    summary="반려동물 초대코드로 공유 요청 생성",
    description="초대코드를 사용하여 반려동물 공유 요청을 생성합니다.",
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
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    반려동물 공유 요청을 생성합니다.
    - pet_search_id: 반려동물 초대코드
    - 요청자는 body 없이 단순 요청 생성
    """
    service = PetShareRequestService(db)
    return service.create_request(
        request=request,
        authorization=authorization,
        pet_search_id=pet_search_id,
    )


# ---------------------------------------------------------
# 2) 공유 요청 승인/거절
# ---------------------------------------------------------
@router.patch(
    "/share/{request_id}",
    summary="반려동물 공유 요청 승인/거절",
    description="반려동물 공유 요청을 승인하거나 거절합니다.",
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
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    반려동물 공유 요청을 승인하거나 거절합니다.
    - request_id: 공유 요청 ID
    - body.status: APPROVED 또는 REJECTED
    - owner만 처리 가능
    """
    service = PetShareRequestService(db)
    return service.approve_request(
        request=request,
        authorization=authorization,
        request_id=request_id,
        body=body,
    )

    # 승인요청 조회 리스트 생성

@router.get(
    "/share/requests/me",
    summary="내가 보낸 공유 요청 리스트 조회",
    description="로그인한 사용자가 보낸 반려동물 공유 요청 목록을 조회합니다.",
    response_model=MyShareRequestListResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
def get_my_share_requests(
    request: Request,
    status: Optional[str] = None,
    page: int = 0,
    size: int = 20,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    service = PetShareRequestService(db)
    return service.get_my_requests(
        request=request,
        authorization=authorization,
        status=status,
        page=page,
        size=size,
    )
