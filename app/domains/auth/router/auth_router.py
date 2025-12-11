from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.auth.service.auth_service import AuthService
from app.schemas.auth.auth_schema import LoginResponse
from app.schemas.error_schema import ErrorResponse
from fastapi import status
from app.domains.auth.exception import AUTH_LOGIN_RESPONSES, AUTH_DELETE_RESPONSES

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    summary="Firebase 토큰으로 로그인",
    description="Firebase ID 토큰을 사용하여 사용자를 인증하고 로그인합니다. 신규 사용자는 자동으로 생성됩니다.",
    status_code=200,
    response_model=LoginResponse,
    responses=AUTH_LOGIN_RESPONSES,
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


@router.delete(
    "/delete",
    summary="회원 탈퇴",
    description="사용자가 속한 모든 family를 처리한 후 계정을 삭제합니다.",
    status_code=status.HTTP_200_OK,
    responses=AUTH_DELETE_RESPONSES,
)
def delete_account(
    request: Request,
    authorization: str | None = Header(None, description="Firebase ID 토큰 (Bearer 토큰 형식)"),
    db: Session = Depends(get_db)
):
    return AuthService.delete_account(request, authorization, db)
