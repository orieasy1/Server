# app/domains/notifications/router/sos_router.py

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.notifications.service.sos_service import SosService
from app.schemas.notifications.sos_schema import SosRequestSchema, SosResponseSchema
from app.schemas.error_schema import ErrorResponse

router = APIRouter(prefix="/api/v1/notifications", tags=["SOS"])


@router.post(
    "/sos",
    summary="SOS 긴급 알림 전송",
    description="디바이스 쉐이킹 시 가족 전원에게 SOS 알림을 전송합니다.",
    response_model=SosResponseSchema,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
def send_sos(
    request: Request,
    body: SosRequestSchema,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    firebase_token = None
    if authorization and authorization.startswith("Bearer "):
        firebase_token = authorization.split(" ")[1]

    service = SosService(db)
    return service.send_sos(
        request=request,
        firebase_token=firebase_token,
        body=body
    )

