from pydantic import BaseModel

class PetImageResponse(BaseModel):
    success: bool = True
    status: int = 200
    image_url: str
    timeStamp: str
    path: str
