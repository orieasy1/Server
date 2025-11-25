from sqlalchemy import Column, Integer, DECIMAL, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class ActivityStat(Base):
    __tablename__ = "activity_stats"

    stats_id = Column(Integer, primary_key=True, autoincrement=True)
    pet_id = Column(Integer, ForeignKey("pets.pet_id"), nullable=False)

    date = Column(Date, nullable=False)
    total_walks = Column(Integer, default=0)
    total_distance_km = Column(Float)
    total_duration_min = Column(Integer, default=0)
    avg_speed_kmh = Column(Float)
    calories_burned = Column(Float)

    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
