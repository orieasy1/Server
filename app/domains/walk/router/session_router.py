from fastapi import APIRouter, Header, Request, Depends, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.session_service import SessionService
from app.schemas.walk.session_schema import WalkStartRequest, WalkStartResponse, WalkTrackRequest, WalkTrackResponse, WalkEndRequest, WalkEndResponse
from app.domains.walk.exception import (
    SESSION_START_RESPONSES,
    SESSION_TRACK_RESPONSES,
    SESSION_END_RESPONSES,
)


router = APIRouter(
    prefix="/api/v1/walk",
    tags=["Walk"]
)


@router.post(
    "/sessions/start",
    summary="산책 시작",
    description="새로운 산책 세션을 시작합니다. 진행 중인 산책이 있으면 시작할 수 없습니다.",
    status_code=201,
    response_model=WalkStartResponse,
    responses=SESSION_START_RESPONSES,
)
def start_walk(
    request: Request,
    body: WalkStartRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    새로운 산책 세션을 시작합니다.
    
    - body: 산책 시작 정보 (pet_id, start_lat, start_lng)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 시작 가능
    - 진행 중인 산책이 있으면 409 에러 반환
    - GPS 좌표는 optional이지만 둘 다 있거나 둘 다 없어야 함
    - start_time은 서버 기준으로 기록
    """
    service = SessionService(db)
    return service.start_walk(
        request=request,
        authorization=authorization,
        body=body,
    )


@router.post(
    "/sessions/{walk_id}/track",
    summary="산책 위치 기록",
    description="산책 중 실시간 위치 정보를 기록합니다. 종료된 산책에는 기록할 수 없습니다.",
    status_code=201,
    response_model=WalkTrackResponse,
    responses=SESSION_TRACK_RESPONSES,
)
def track_walk(
    request: Request,
    walk_id: int = Path(..., description="산책 세션 ID"),
    body: WalkTrackRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 중 실시간 위치 정보를 기록합니다.
    
    - walk_id: 산책 세션 ID (path parameter)
    - body: 위치 정보 (latitude, longitude, timestamp)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 기록 가능
    - 종료된 산책 세션에는 기록 불가
    - 위도/경도 유효성 검사 (위도: -90~90, 경도: -180~180)
    """
    service = SessionService(db)
    return service.track_walk(
        request=request,
        authorization=authorization,
        walk_id=walk_id,
        body=body,
    )


@router.post(
    "/sessions/{walk_id}/end",
    summary="산책 종료",
    description="산책 세션을 종료하고 최종 통계를 기록합니다. 활동 통계가 자동으로 업데이트됩니다.",
    status_code=200,
    response_model=WalkEndResponse,
    responses=SESSION_END_RESPONSES,
)
def end_walk(
    request: Request,
    walk_id: int = Path(..., description="산책 세션 ID"),
    body: WalkEndRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 세션을 종료합니다.
    
    - walk_id: 산책 세션 ID (path parameter)
    - body: 산책 종료 정보 (total_distance_km, total_duration_min, last_lat, last_lng, route_data)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 종료 가능
    - 이미 종료된 산책에는 종료 불가
    - activity_stats 자동 업데이트
    """
    service = SessionService(db)
    return service.end_walk(
        request=request,
        authorization=authorization,
        walk_id=walk_id,
        body=body,
    )

