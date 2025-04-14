from pydantic import BaseModel, Field, ConfigDict


class AdvanceTimeRequest(BaseModel):
    current_date: int = Field(..., ge=0)

class AdvanceTimeResponse(BaseModel):
    current_date: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)
