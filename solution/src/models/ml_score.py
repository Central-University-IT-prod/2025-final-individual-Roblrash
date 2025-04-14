from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.backend.database import Base

class MLScore(Base):
    __tablename__ = "ml_scores"
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.client_id"), primary_key=True)
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.advertiser_id"), primary_key=True)
    score = Column(Integer, nullable=False)
