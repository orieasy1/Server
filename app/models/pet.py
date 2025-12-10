from sqlalchemy import Column, Integer, Float, String, DateTime, DECIMAL, Enum, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base
import enum

class PetGender(str, enum.Enum):
    M = "M"
    F = "F"
    Unknown = "Unknown"

class Pet(Base):
    __tablename__ = "pets"

    pet_id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, ForeignKey("families.family_id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    pet_search_id = Column(String(8), unique=True, nullable=False)

    name = Column(String(50), nullable=False)
    breed = Column(String(50))
    age = Column(Integer)
    weight = Column(Float)
    gender = Column(Enum(PetGender), default=PetGender.Unknown, nullable=True)

    disease = Column(String(255))
    image_url = Column(String(255))
    voice_url = Column(String(255))  # 반려동물 음성 녹음 URL

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
