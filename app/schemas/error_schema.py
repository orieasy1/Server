from pydantic import BaseModel
from datetime import datetime

class ErrorResponse(BaseModel):
    success: bool = False
    status: int
    code: str
    reason: str
    timeStamp: str
    path: str
