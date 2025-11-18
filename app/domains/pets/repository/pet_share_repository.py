from sqlalchemy.orm import Session
from typing import Optional

from app.models.pet_share_request import PetShareRequest, RequestStatus
from app.models.family_member import FamilyMember
from app.models.pet import Pet


class PetShareRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------
    # Pet lookup
    # -------------------------------
    def get_pet_by_search_id(self, pet_search_id: str) -> Optional[Pet]:
        return (
            self.db.query(Pet)
            .filter(Pet.pet_search_id == pet_search_id)
            .first()
        )

    # -------------------------------
    # Family membership
    # -------------------------------
    def is_user_in_family(self, user_id: int, family_id: int) -> bool:
        return (
            self.db.query(FamilyMember)
            .filter(
                FamilyMember.user_id == user_id,
                FamilyMember.family_id == family_id
            )
            .first()
            is not None
        )

    # -------------------------------
    # Share Request
    # -------------------------------
    def create_request(self, pet_id: int, requester_id: int, message: str):
        req = PetShareRequest(
            pet_id=pet_id,
            requester_id=requester_id,
            message=message,
            status=RequestStatus.PENDING
        )
        self.db.add(req)
        self.db.flush()
        return req

    def exists_pending_request(self, pet_id: int, requester_id: int) -> bool:
        return (
            self.db.query(PetShareRequest)
            .filter(
                PetShareRequest.pet_id == pet_id,
                PetShareRequest.requester_id == requester_id,
                PetShareRequest.status == RequestStatus.PENDING
            )
            .first()
            is not None
        )

    def get_request_by_id(self, request_id: int) -> Optional[PetShareRequest]:
        return self.db.get(PetShareRequest, request_id)

    def update_request_status(self, req: PetShareRequest, status: RequestStatus):
        req.status = status
        self.db.flush()
        return req
