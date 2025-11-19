from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.users.service.user_service import UserService
from app.schemas.users.user_update_schema import UserUpdateRequest
from app.schemas.error_schema import ErrorResponse

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    summary="내 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다.",
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def get_me(
    request: Request,
    authorization: str | None = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자의 정보를 조회합니다.
    
    - Authorization 헤더의 토큰에서 사용자 정보를 추출
    - 사용자 ID, 닉네임, 이메일, 프로필 이미지 등 반환
    """
    return UserService.get_me(request, authorization, db)

@router.patch(
    "/me",
    summary="내 정보 수정",
    description="현재 로그인한 사용자의 정보를 수정합니다.",
    status_code=200,
    responses={
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        401: {"model": ErrorResponse, "description": "인증 실패"},
        404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 내부 오류"},
    },
)
def update_me(
    request: Request,
    authorization: str | None = Header(None, description="Firebase ID 토큰"),
    body: UserUpdateRequest = None,
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자의 정보를 수정합니다.
    
    - body: 수정할 사용자 정보 (닉네임, 프로필 이미지 등)
    - 전송한 필드만 업데이트됨
    """
    return UserService.update_me(request, authorization, body, db)