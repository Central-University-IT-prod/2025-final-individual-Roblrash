from pydantic import BaseModel, Field

class AdTextRequest(BaseModel):
    ad_title: str = Field(..., min_length=1)
    advertiser_name: str = Field(..., min_length=1)

class AdTextResponse(BaseModel):
    ad_text: str
