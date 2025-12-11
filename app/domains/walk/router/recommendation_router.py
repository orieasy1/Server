from fastapi import APIRouter, Header, Request, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.recommendation_service import RecommendationService
from app.domains.walk.service.walk_recommendation_service import WalkRecommendationService
from app.domains.walk.exception import RECOMMEND_RESPONSES
from app.schemas.walk.recommendation_schema import RecommendationResponse
from app.schemas.walk.walk_recommendation_request_schema import WalkRecommendationRequest


router = APIRouter(
    prefix="/api/v1/walk",
    tags=["Walk"]
)


@router.get(
    "/recommendations",
    summary="추천 산책 정보 조회",
    description="반려동물의 특성에 맞는 추천 산책 정보를 조회합니다.",
    status_code=200,
    response_model=RecommendationResponse,
    responses=RECOMMEND_RESPONSES,
)
def get_recommendation(
    request: Request,
    pet_id: int = Query(..., description="반려동물 ID"),
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    선택된 반려동물의 추천 산책 정보를 조회합니다.
    
    - pet_id: 반려동물 ID (query parameter)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 조회 가능
    """
    service = RecommendationService(db)
    return service.get_recommendation(
        request=request,
        authorization=authorization,
        pet_id=pet_id,
    )


@router.post(
    "/recommendation",
    summary="산책 추천 멘트 생성",
    description="펫 정보와 날씨를 바탕으로 OpenAI로 산책 추천 멘트를 생성합니다.",
    status_code=200,
    response_model=RecommendationResponse,
    responses=RECOMMEND_RESPONSES,
)
def create_walk_recommendation(
    request: Request,
    body: WalkRecommendationRequest = ...,
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 추천 멘트를 생성합니다.
    
    - body: 펫 ID, 위치, 날씨 정보, 오늘 산책 현황
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 가능
    - 날씨 정보가 없으면 위치 기반으로 자동 조회
    - OpenAI를 사용하여 개인화된 추천 멘트 생성
    """
    service = WalkRecommendationService(db)
    return service.generate_recommendation(
        request=request,
        authorization=authorization,
        body=body,
    )
