from pydantic import BaseModel, Field

class ModerationToggleRequest(BaseModel):
    enabled: bool = Field(..., description="True — включить модерацию, False — отключить модерацию")

class ModerationToggleResponse(BaseModel):
    moderation_enabled: bool