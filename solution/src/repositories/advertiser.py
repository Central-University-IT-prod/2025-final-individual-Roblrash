from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.models.advertiser import Advertiser
from src.schemas.advertiser import AdvertiserUpsert

class AdvertiserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, advertiser_id: UUID) -> Advertiser:
        stmt = select(Advertiser).where(Advertiser.advertiser_id == advertiser_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert(self, adv_data: AdvertiserUpsert) -> Advertiser:
        adv = await self.get_by_id(adv_data.advertiser_id)
        if adv:
            adv.name = adv_data.name
        else:
            adv = Advertiser(**adv_data.model_dump(by_alias=True))
            self.session.add(adv)
        await self.session.commit()
        await self.session.refresh(adv)
        return adv

    async def upsert_many(self, advertisers: list[AdvertiserUpsert]) -> list[Advertiser]:
        results = []
        for adv in advertisers:
            updated = await self.upsert(adv)
            results.append(updated)
        return results
