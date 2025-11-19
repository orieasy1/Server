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
    description="초대코드를 사용하여 반려동물 공유 요청을 생성합니다.",
    status_code=201,
    response_model=PetShareRequestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "이미 공유 요청이 존재함"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
async def create_pet_share_request(
    pet_search_id: str,
    request: Request,
    body: PetShareRequestCreate,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    반려동물 공유 요청을 생성합니다.
    
    - pet_search_id: 반려동물의 초대코드 (path parameter)
    - body: 공유 요청 정보 (선택적 메시지 포함)
    - 요청자는 해당 반려동물의 가족 구성원으로 추가 요청
    """
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
    description="반려동물 공유 요청을 승인하거나 거절합니다.",
    status_code=200,
    response_model=PetShareApproveResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음 (소유자만 승인/거절 가능)"},
        404: {"model": ErrorResponse, "description": "공유 요청을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "이미 처리된 요청"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
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
    
    - request_id: 공유 요청 ID (path parameter)
    - body: 승인/거절 상태 (APPROVED 또는 REJECTED)
    - 권한: 해당 반려동물의 owner만 승인/거절 가능
    - 승인 시 요청자가 가족 구성원으로 추가됨
    """
    service = PetShareRequestService(db)
    return service.approve_request(
        request=request,
        authorization=authorization,
        request_id=request_id,
        body=body,
    )
