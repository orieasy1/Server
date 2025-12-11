from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db import get_db
from app.domains.users.service.user_service import UserService
from app.domains.users.exception import USER_GET_RESPONSES, USER_EDIT_RESPONSES, FCM_UPDATE_RESPONSES

from app.schemas.users.user_update_schema import UserUpdateRequest
from app.schemas.users.user_response_schema import UserMeResponse
from app.schemas.error_schema import ErrorResponse


# FCM 토큰 업데이트 요청 스키마
class FcmTokenUpdateRequest(BaseModel):
    fcm_token: str
    device_id: Optional[str] = None
    platform: Optional[str] = "android"


# FCM 토큰 업데이트 응답 스키마
class FcmTokenUpdateResponse(BaseModel):
    success: bool
    status: int
    message: str


router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    summary="내 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다.",
    status_code=200,
    response_model=UserMeResponse,
    responses=USER_GET_RESPONSES,
)
def get_me(
    request: Request,
    authorization: str | None = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db)
):
    return UserService.get_me(request, authorization, db)


@router.patch(
    "/me",
    summary="내 정보 수정",
    description="현재 로그인한 사용자의 정보를 수정합니다.",
    status_code=200,
    response_model=UserMeResponse,
    responses=USER_EDIT_RESPONSES,
)
def update_me(
    request: Request,
    authorization: str | None = Header(None, description="Firebase ID 토큰"),
    body: UserUpdateRequest = None,
    db: Session = Depends(get_db)
):
    return UserService.update_me(request, authorization, body, db)


@router.put(
    "/me/fcm-token",
    summary="FCM 토큰 업데이트",
    description="사용자의 FCM 푸시 알림 토큰을 업데이트합니다.",
    status_code=200,
    response_model=FcmTokenUpdateResponse,
    responses=FCM_UPDATE_RESPONSES,
)
def update_fcm_token(
    request: Request,
    body: FcmTokenUpdateRequest,
    authorization: str | None = Header(None, description="Firebase ID 토큰"),
    db: Session = Depends(get_db)
):
    """
    FCM 푸시 알림 토큰을 서버에 저장합니다.
    앱이 시작되거나 FCM 토큰이 갱신될 때 호출됩니다.
    """
    return UserService.update_fcm_token(
        request=request,
        authorization=authorization,
        fcm_token=body.fcm_token,
        db=db,
        device_id=body.device_id,
        platform=body.platform,
    )
