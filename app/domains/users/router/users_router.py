from fastapi import APIRouter, Header, Request, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domains.users.service.user_service import UserService
from app.schemas.users.user_update_schema import UserUpdateRequest

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me")
def get_me(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):
    return UserService.get_me(request, authorization, db)

@router.patch("/me")
def update_me(
    request: Request,
    authorization: str | None = Header(None),
    body: UserUpdateRequest = None,
    db: Session = Depends(get_db)
):
    return UserService.update_me(request, authorization, body, db)