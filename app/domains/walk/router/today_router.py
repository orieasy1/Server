from fastapi import APIRouter, Header, Request, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.today_service import TodayService
from app.schemas.walk.today_schema import TodayWalkResponse
from app.domains.walk.exception import TODAY_RESPONSES


router = APIRouter(
    prefix="/api/v1/walk",
    tags=["Walk"]
)


@router.get(
    "/today",
    summary="오늘 산책 현황 조회",
    description="오늘 날짜 기준으로 반려동물의 산책 현황을 조회합니다.",
    status_code=200,
    response_model=TodayWalkResponse,
    responses=TODAY_RESPONSES,
)
def get_today_walks(
    request: Request,
    pet_id: int = Query(..., description="반려동물 ID"),
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    오늘의 산책 현황을 조회합니다.
    
    - pet_id: 반려동물 ID (query parameter)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 조회 가능
    - 오늘 날짜 기준으로 산책 통계 제공:
        - 누적 횟수 (완료된 산책)
        - 총 산책 시간
        - 총 이동 거리
        - 지금 몇 번째 산책인지
        - 진행 중인 산책이 있는지
    """
    service = TodayService(db)
    return service.get_today_walks(
        request=request,
        authorization=authorization,
        pet_id=pet_id,
    )

