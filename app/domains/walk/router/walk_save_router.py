from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.db import get_db
from app.domains.walk.service.walk_save_service import WalkSaveService
from app.schemas.walk.walk_save_schema import WalkSaveRequest, WalkSaveResponse
from app.domains.walk.exception import SAVE_RESPONSES, NOTIFY_RESPONSES


# 산책 시작 알림 요청 스키마
class WalkStartNotifyRequest(BaseModel):
    pet_id: int = Field(..., description="반려동물 ID")


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
    responses=SAVE_RESPONSES,
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


@router.post(
    "/walks/notify-start",
    summary="산책 시작 알림 전송",
    description="산책 시작 시 가족 멤버들에게 알림을 전송합니다.",
    status_code=200,
    responses=NOTIFY_RESPONSES,
)
def notify_walk_start(
    request: Request,
    body: WalkStartNotifyRequest,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 시작 시 가족 멤버들에게 알림을 전송합니다.
    
    - body: pet_id (산책할 반려동물 ID)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 가능
    - 가족 멤버들에게 푸시 알림 + DB 알림 저장
    """
    service = WalkSaveService(db)
    return service.notify_walk_start(
        request=request,
        authorization=authorization,
        pet_id=body.pet_id,
    )


