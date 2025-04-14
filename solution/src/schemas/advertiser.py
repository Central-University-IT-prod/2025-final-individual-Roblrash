from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID

class AdvertiserOut(BaseModel):
    advertiser_id: UUID
    name: str = Field(..., min_length=1)

    model_config = ConfigDict(from_attributes=True)

class AdvertiserUpsert(BaseModel):
    advertiser_id: UUID
    name: str = Field(..., min_length=1)
