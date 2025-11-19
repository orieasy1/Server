from pydantic import BaseModel, Field
from typing import List, Optional


class Range(BaseModel):
    """기간 범위"""
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")


class GoalSummary(BaseModel):
    """목표 요약"""
    has_goal: bool = Field(..., description="목표 설정 여부")
    target_walks_per_day: Optional[int] = Field(None, description="일일 목표 산책 횟수")
    target_minutes_per_day: Optional[int] = Field(None, description="일일 목표 산책 시간 (분)")
    target_distance_km_per_day: Optional[float] = Field(None, description="일일 목표 산책 거리 (km)")
    achievement_rate_walks: Optional[float] = Field(None, description="산책 횟수 달성률 (%)")
    achievement_rate_minutes: Optional[float] = Field(None, description="산책 시간 달성률 (%)")
    achievement_rate_distance: Optional[float] = Field(None, description="산책 거리 달성률 (%)")


class RecommendationSummary(BaseModel):
    """추천 요약"""
    has_recommendation: bool = Field(..., description="추천 정보 존재 여부")
    recommended_walks_per_day: Optional[int] = Field(None, description="일일 추천 산책 횟수")
    recommended_minutes_per_day: Optional[int] = Field(None, description="일일 추천 산책 시간 (분)")
    recommended_distance_km_per_day: Optional[float] = Field(None, description="일일 추천 산책 거리 (km)")


class Summary(BaseModel):
    """활동 통계 요약"""
    pet_id: int = Field(..., description="반려동물 ID")
    total_walks: int = Field(..., description="총 산책 횟수")
    total_distance_km: float = Field(..., description="총 산책 거리 (km)")
    total_duration_min: int = Field(..., description="총 산책 시간 (분)")
    active_days: int = Field(..., description="활동한 날짜 수")
    total_days: int = Field(..., description="전체 날짜 수")
    avg_walks_per_day: float = Field(..., description="일평균 산책 횟수")
    avg_distance_km_per_day: float = Field(..., description="일평균 산책 거리 (km)")
    avg_duration_min_per_day: float = Field(..., description="일평균 산책 시간 (분)")
    goal: GoalSummary = Field(..., description="목표 요약")
    recommendation: RecommendationSummary = Field(..., description="추천 요약")


class ChartPoint(BaseModel):
    """차트 포인트"""
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    total_walks: int = Field(..., description="총 산책 횟수")
    total_distance_km: float = Field(..., description="총 산책 거리 (km)")
    total_duration_min: int = Field(..., description="총 산책 시간 (분)")
    goal_walks: Optional[int] = Field(None, description="목표 산책 횟수")
    goal_minutes: Optional[int] = Field(None, description="목표 산책 시간 (분)")
    goal_distance_km: Optional[float] = Field(None, description="목표 산책 거리 (km)")


class Chart(BaseModel):
    """차트 데이터"""
    granularity: str = Field(..., description="그래프 단위 (day, week, month)")
    points: List[ChartPoint] = Field(..., description="차트 포인트 목록")


class ActivityStatsResponse(BaseModel):
    """활동 통계 조회 응답"""
    success: bool = Field(True, description="성공 여부")
    status: int = Field(200, description="HTTP 상태 코드")
    period: str = Field(..., description="조회 기간 (daily, weekly, monthly)")
    range: Range = Field(..., description="기간 범위")
    summary: Summary = Field(..., description="활동 통계 요약")
    chart: Chart = Field(..., description="차트 데이터")
    timeStamp: str = Field(..., description="응답 시간 (ISO 형식)")
    path: str = Field(..., description="요청 경로")
