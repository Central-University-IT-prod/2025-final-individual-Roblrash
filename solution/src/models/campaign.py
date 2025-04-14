import uuid
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from src.backend.database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.advertiser_id"), nullable=False)
    impressions_limit = Column(Integer, nullable=False)
    clicks_limit = Column(Integer, nullable=False)
    cost_per_impression = Column(Numeric, nullable=False)
    cost_per_click = Column(Numeric, nullable=False)
    ad_title = Column(String, nullable=False)
    ad_text = Column(String, nullable=False)
    start_date = Column(Integer, nullable=False)
    end_date = Column(Integer, nullable=False)
    targeting = Column(JSON, nullable=True, default={})
    image_url = Column(String, nullable=True)
