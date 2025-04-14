from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class MLScore(BaseModel):
    client_id: UUID
    advertiser_id: UUID
    score: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)