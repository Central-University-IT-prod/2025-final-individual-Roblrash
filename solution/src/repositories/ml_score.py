from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.models.ml_score import MLScore
from src.schemas.ml_score import MLScore as MLScoreSchema

class MLScoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_ids(self, client_id: UUID, advertiser_id: UUID) -> MLScore:
        stmt = select(MLScore).where(
            MLScore.client_id == client_id,
            MLScore.advertiser_id == advertiser_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert(self, ml_data: MLScoreSchema) -> MLScore:
        existing = await self.get_by_ids(ml_data.client_id, ml_data.advertiser_id)
        if existing:
            existing.score = ml_data.score
        else:
            new_ml = MLScore(**ml_data.model_dump())
            self.session.add(new_ml)
            existing = new_ml
        await self.session.commit()
        await self.session.refresh(existing)
        return existing
