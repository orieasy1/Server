from fastapi import APIRouter, Header, Request, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.goal_service import GoalService
from app.schemas.error_schema import ErrorResponse
from app.schemas.walk.goal_schema import WalkGoalRequest, WalkGoalResponse, WalkGoalPatchRequest


router = APIRouter(
    prefix="/api/v1/walk",
    tags=["Walk"]
)


@router.post(
    "/goals",
    summary="목표 산책량 설정",
    description="반려동물의 목표 산책량을 설정합니다. 기존 목표가 있으면 업데이트됩니다.",
    status_code=200,
    response_model=WalkGoalResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (유효하지 않은 값 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def set_walk_goal(
    request: Request,
    pet_id: int = Query(..., description="반려동물 ID"),
    body: WalkGoalRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    목표 산책량을 설정합니다.
    
    - pet_id: 반려동물 ID (query parameter)
    - body: 목표 산책량 정보 (target_walks, target_minutes, target_distance_km)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 설정 가능
    - 기존 목표가 있으면 업데이트, 없으면 생성
    - 유효성 검사: 필수 필드, 형식, 0보다 큰 값, 건강에 무리가 가는 수준 체크
    """
    service = GoalService(db)
    return service.set_goal(
        request=request,
        authorization=authorization,
        pet_id=pet_id,
        body=body,
    )


@router.patch(
    "/goals/{goal_id}",
    summary="목표 산책량 수정",
    description="기존 목표 산책량을 부분적으로 수정합니다.",
    status_code=200,
    response_model=WalkGoalResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음 (소유자만 수정 가능)"},
        404: {"model": ErrorResponse, "description": "목표를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def patch_walk_goal(
    request: Request,
    goal_id: int = Path(..., description="목표 산책량 ID"),
    body: WalkGoalPatchRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    목표 산책량을 부분 수정합니다.
    
    - goal_id: 목표 산책량 ID (path parameter)
    - body: 수정할 목표 산책량 정보 (일부 필드만 수정 가능)
    - 권한 체크: 해당 반려동물의 owner만 수정 가능
    - 유효성 검사: 수정할 필드 존재 여부, 형식, 0보다 큰 값, 건강에 무리가 가는 수준 체크
    """
    service = GoalService(db)
    return service.patch_goal(
        request=request,
        authorization=authorization,
        goal_id=goal_id,
        body=body,
    )

