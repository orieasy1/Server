from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.walk_save_service import WalkSaveService
from app.schemas.error_schema import ErrorResponse
from app.schemas.walk.walk_save_schema import WalkSaveRequest, WalkSaveResponse

router = APIRouter(
    prefix="/api/v1",
    tags=["Walk"]
)


@router.post(
    "/walks",
    summary="산책 기록 저장",
    description="산책 기록을 저장합니다. 저장된 기록은 Record/Activity 페이지에서 조회할 수 있습니다.",
    status_code=200,
    response_model=WalkSaveResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (필수 필드 누락, 날짜 형식 오류 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def save_walk(
    request: Request,
    body: WalkSaveRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 기록을 저장합니다.
    
    - body: 산책 기록 정보 (pet_id, start_time, end_time, duration_min, distance_km 등)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 저장 가능
    - route_points가 있으면 경로 포인트도 함께 저장
    - 저장된 기록은 Record/Activity 페이지에서 조회 가능
    """
    service = WalkSaveService(db)
    return service.save_walk(
        request=request,
        authorization=authorization,
        body=body,
    )


