from sqlalchemy.orm import Session
from app.models.family import Family


class FamilyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_family(self, family_name: str) -> Family:
        family = Family(family_name=family_name)
        self.db.add(family)
        self.db.flush()
        return family
