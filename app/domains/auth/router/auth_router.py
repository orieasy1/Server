from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.auth.service.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login")
def login(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    return AuthService.login(request, authorization, db)
