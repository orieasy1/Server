from fastapi import APIRouter, Header, Request, Depends, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.domains.walk.service.recommendation_service import RecommendationService
from app.domains.walk.service.today_service import TodayService
from app.domains.walk.service.goal_service import GoalService
from app.domains.walk.service.session_service import SessionService
from app.domains.walk.service.weather_service import WeatherService
from app.domains.walk.service.photo_service import PhotoService
from app.schemas.error_schema import ErrorResponse
from app.schemas.walk.recommendation_schema import RecommendationResponse
from app.schemas.walk.today_schema import TodayWalkResponse
from app.schemas.walk.goal_schema import WalkGoalRequest, WalkGoalResponse, WalkGoalPatchRequest
from app.schemas.walk.session_schema import WalkStartRequest, WalkStartResponse, WalkTrackRequest, WalkTrackResponse, WalkEndRequest, WalkEndResponse
from app.schemas.walk.weather_schema import WeatherResponse
from app.schemas.walk.photo_schema import PhotoUploadResponse


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
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
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


@router.get(
    "/today",
    summary="오늘 산책 현황 조회",
    description="오늘 날짜 기준으로 반려동물의 산책 현황을 조회합니다.",
    status_code=200,
    response_model=TodayWalkResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
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


@router.post(
    "/sessions/start",
    summary="산책 시작",
    description="새로운 산책 세션을 시작합니다. 진행 중인 산책이 있으면 시작할 수 없습니다.",
    status_code=201,
    response_model=WalkStartResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (GPS 좌표 형식 오류 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "반려동물을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "이미 진행 중인 산책이 있음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
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
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (위도/경도 범위 초과 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "산책을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "이미 종료된 산책"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
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
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "산책을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "이미 종료된 산책"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
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


@router.get(
    "/weather",
    summary="날씨 정보 조회",
    description="현재 위치 기반 날씨 정보를 조회합니다. 인증은 선택사항이며, 외부 API를 통해 조회됩니다.",
    status_code=200,
    response_model=WeatherResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (위도/경도 누락 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패 (선택적)"},
        502: {"model": ErrorResponse, "description": "외부 API 게이트웨이 오류"},
        503: {"model": ErrorResponse, "description": "외부 API 서비스 불가"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def get_weather(
    request: Request,
    lat: Optional[float] = Query(None, description="위도 (-90 ~ 90)"),
    lng: Optional[float] = Query(None, description="경도 (-180 ~ 180)"),
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰 (선택적)"),
):
    """
    현재 위치 기반 날씨 정보를 조회합니다.
    
    - lat: 위도 (query parameter, 필수)
    - lng: 경도 (query parameter, 필수)
    - Authorization: 옵션 (비로그인 허용 가능)
    - 외부 API 연동 (OpenWeatherMap)
    - 캐싱 (10분 간격)
    - 외부 API 장애 시 오래된 캐시 반환 (is_stale=true)
    """
    service = WeatherService()
    return service.get_weather(
        request=request,
        authorization=authorization,
        lat=lat,
        lng=lng,
    )


@router.post(
    "/sessions/{walk_id}/photo",
    summary="산책 사진 업로드",
    description="산책 종료 후 인증 사진을 업로드합니다. 종료된 산책에만 업로드 가능합니다.",
    status_code=201,
    response_model=PhotoUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (파일 형식/크기 오류 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "산책을 찾을 수 없음"},
        409: {"model": ErrorResponse, "description": "진행 중인 산책에는 업로드 불가"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def upload_walk_photo(
    request: Request,
    walk_id: int = Path(..., description="산책 세션 ID"),
    file: UploadFile = File(..., description="이미지 파일 (JPG, PNG, 최대 10MB)"),
    caption: Optional[str] = Form(None, description="사진 설명"),
    photo_timestamp: Optional[str] = Form(None, description="사진 촬영 시간 (ISO 형식)"),
    authorization: Optional[str] = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db),
):
    """
    산책 종료 후 인증 사진을 업로드합니다.
    
    - walk_id: 산책 세션 ID (path parameter)
    - file: 이미지 파일 (multipart/form-data, 필수)
    - caption: 사진 설명 (선택)
    - photo_timestamp: 사진 촬영 시간 (선택, 산책 시간 검증용)
    - 권한 체크: 해당 반려동물의 family_members에 속한 사용자만 업로드 가능
    - 종료된 산책에만 업로드 가능
    - 파일 형식: JPG, PNG
    - 파일 크기: 최대 10MB
    """
    service = PhotoService(db)
    return service.upload_photo(
        request=request,
        authorization=authorization,
        walk_id=walk_id,
        file=file,
        caption=caption,
        photo_timestamp=photo_timestamp,
    )

