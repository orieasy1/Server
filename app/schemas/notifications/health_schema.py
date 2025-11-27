# app/schemas/notifications/health_schema.py

from pydantic import BaseModel

class HealthFeedbackRequest(BaseModel):
    pet_id: int
