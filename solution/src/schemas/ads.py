from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class Ad(BaseModel):
    ad_id: UUID
    ad_title: str = Field(..., min_length=1)
    ad_text: str = Field(..., min_length=1)
    advertiser_id: UUID
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ClickRequest(BaseModel):
    client_id: UUID
