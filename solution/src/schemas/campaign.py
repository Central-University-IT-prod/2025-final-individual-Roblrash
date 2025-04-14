from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Any
from uuid import UUID
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    ALL = "ALL"

class Targeting(BaseModel):
    gender: Optional[GenderEnum] = None
    age_from: Optional[int] = Field(None, ge=0, le=120)
    age_to: Optional[int] = Field(None, ge=0, le=120)
    location: Optional[str] = None

    @field_validator("age_to")
    @classmethod
    def age_to_after_age_from(cls, v, info):
        data = info.data
        age_from = data.get("age_from")
        if age_from is not None and v is not None and v < age_from:
            raise ValueError("Значение age_to должно быть не меньше значения age_from")
        return v

class CampaignCreate(BaseModel):
    impressions_limit: int = Field(..., gt=0)
    clicks_limit: int = Field(..., gt=0)
    cost_per_impression: float = Field(..., gt=0)
    cost_per_click: float = Field(..., gt=0)
    ad_title: str = Field(..., min_length=1)
    ad_text: str = Field(..., min_length=1)
    start_date: int = Field(..., ge=0)
    end_date: int = Field(..., ge=0)
    targeting: Optional[Targeting] = None

    @field_validator("end_date")
    @classmethod
    def end_day_after_start_day(cls, v, info):
        data = info.data
        if "start_date" in data and v < data["start_date"]:
            raise ValueError("День окончания должен быть не раньше дня начала")
        return v

    @field_validator("clicks_limit")
    @classmethod
    def clicks_limit_not_exceed_impressions_limit(cls, v, info):
        data = info.data
        if "impressions_limit" in data and v > data["impressions_limit"]:
            raise ValueError("Лимит кликов не может быть больше лимита показов")
        return v

class CampaignUpdate(BaseModel):
    impressions_limit: int = Field(..., gt=0)
    clicks_limit: int = Field(..., gt=0)
    cost_per_impression: float = Field(..., gt=0)
    cost_per_click: float = Field(..., gt=0)
    ad_title: str = Field(..., min_length=1)
    ad_text: str = Field(..., min_length=1)
    start_date: int = Field(..., ge=0)
    end_date: int = Field(..., ge=0)
    targeting: Targeting

    @field_validator("end_date")
    @classmethod
    def end_day_after_start_day(cls, v, info):
        data = info.data
        if "start_date" in data and v < data["start_date"]:
            raise ValueError("День окончания должен быть не раньше дня начала")
        return v

class CampaignOut(BaseModel):
    campaign_id: UUID
    advertiser_id: UUID
    impressions_limit: int
    clicks_limit: int
    cost_per_impression: float
    cost_per_click: float
    ad_title: str
    ad_text: str
    start_date: int
    end_date: int
    targeting: dict[str, Any] = Field(default_factory=dict)
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
