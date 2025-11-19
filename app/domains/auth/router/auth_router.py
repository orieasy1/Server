from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.auth.service.auth_service import AuthService
from app.schemas.auth.auth_schema import LoginResponse
from app.schemas.error_schema import ErrorResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    summary="Firebase 토큰으로 로그인",
    description="Firebase ID 토큰을 사용하여 사용자를 인증하고 로그인합니다. 신규 사용자는 자동으로 생성됩니다.",
    status_code=200,
    response_model=LoginResponse,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청 (토큰 형식 오류 등)"},
        401: {"model": ErrorResponse, "description": "인증 실패 (유효하지 않은 토큰)"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def login(
    request: Request,
    authorization: str | None = Header(None, description="Firebase ID 토큰 (Bearer 토큰 형식)"),
    db: Session = Depends(get_db)
):
    """
    Firebase ID 토큰을 사용하여 사용자를 인증합니다.
    
    - Authorization 헤더에 Firebase ID 토큰을 포함하여 요청
    - 토큰에서 사용자 정보를 추출하여 DB에 저장/업데이트
    - 신규 사용자는 자동으로 생성되고 is_new_user=true 반환
    - 기존 사용자는 is_new_user=false 반환
    """
    return AuthService.login(request, authorization, db)
