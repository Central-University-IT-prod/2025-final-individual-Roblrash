from pydantic import BaseModel, Field

class Stats(BaseModel):
    impressions_count: int = Field(..., ge=0)
    clicks_count: int = Field(..., ge=0)
    conversion: float
    spent_impressions: float = Field(..., ge=0)
    spent_clicks: float = Field(..., ge=0)
    spent_total: float = Field(..., ge=0)

class DailyStats(BaseModel):
    date: int = Field(..., ge=0)
    impressions_count: int = Field(..., ge=0)
    clicks_count: int = Field(..., ge=0)
    conversion: float
    spent_impressions: float = Field(..., ge=0)
    spent_clicks: float = Field(..., ge=0)
    spent_total: float = Field(..., ge=0)