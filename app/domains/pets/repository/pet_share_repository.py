from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime

from app.models.pet import Pet
from app.models.user import User
from app.models.family_member import FamilyMember
from app.models.pet_share_request import PetShareRequest, RequestStatus


class PetShareRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_pet_by_search_id(self, pet_search_id: str) -> Optional[Pet]:
        return (
            self.db.query(Pet)
            .filter(Pet.pet_id.isnot(None))
            .filter(Pet.pet_search_id == pet_search_id)
            .first()
        )

    def is_user_in_family(self, user_id: int, family_id: int) -> bool:
        return (
            self.db.query(FamilyMember)
            .filter(and_(
                FamilyMember.user_id == user_id,
                FamilyMember.family_id == family_id
            ))
            .first()
            is not None
        )

    def exists_pending_request(self, pet_id: int, requester_id: int) -> bool:
        return (
            self.db.query(PetShareRequest)
            .filter(and_(
                PetShareRequest.pet_id == pet_id,
                PetShareRequest.requester_id == requester_id,
                PetShareRequest.status == RequestStatus.PENDING,
            ))
            .first()
            is not None
        )

    def create_request(self, pet_id: int, requester_id: int, message: Optional[str]) -> PetShareRequest:
        req = PetShareRequest(
            pet_id=pet_id,
            requester_id=requester_id,
            status=RequestStatus.PENDING,
            message=message
        )
        self.db.add(req)
        self.db.flush()
        return req

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).get(user_id)

    def get_request_by_id(self, request_id: int) -> Optional[PetShareRequest]:
        return self.db.query(PetShareRequest).get(request_id)

    def update_request_status(self, req: PetShareRequest, status: RequestStatus) -> PetShareRequest:
        req.status = status
        req.responded_at = datetime.utcnow()
        self.db.flush()
        return req
