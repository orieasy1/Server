from pydantic import BaseModel, Field
from typing import List, Optional


class MyPetItem(BaseModel):
    pet_id: int
    family_id: int
    family_name: Optional[str] = None
    owner_id: int
    is_owner: bool
    name: str
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MyPetsResponse(BaseModel):
    success: bool = Field(True)
    status: int = Field(200)
    pets: List[MyPetItem] = Field(default_factory=list)
    timeStamp: str
    path: str
