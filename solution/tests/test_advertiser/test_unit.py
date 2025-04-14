import pytest
from uuid import uuid4
from src.repositories.advertiser import AdvertiserRepository
from src.repositories.campaign import CampaignRepository
from src.repositories.user import UserRepository
from src.repositories.ml_score import MLScoreRepository
from src.schemas.advertiser import AdvertiserUpsert
from src.schemas.campaign import CampaignCreate, CampaignUpdate, Targeting
from src.schemas.client import ClientUpsert
from src.schemas.ml_score import MLScore
from src.backend.cache import redis_client


# Тест для проверки создания/обновления рекламодателя через репозиторий.
@pytest.mark.asyncio
async def test_advertiser_repository(session):
    repo = AdvertiserRepository(session)
    adv_id = uuid4()
    adv_data = AdvertiserUpsert(advertiser_id=adv_id, name="Test Advertiser")
    adv = await repo.upsert(adv_data)
    assert adv.advertiser_id == adv_id
    assert adv.name == "Test Advertiser"

# Тест для проверки bulk‑операции для рекламодателей.
@pytest.mark.asyncio
async def test_advertiser_upsert_many(session):
    repo = AdvertiserRepository(session)
    adv_ids = [uuid4(), uuid4()]
    adv_data_list = [
        AdvertiserUpsert(advertiser_id=adv_ids[0], name="Bulk Advertiser 1"),
        AdvertiserUpsert(advertiser_id=adv_ids[1], name="Bulk Advertiser 2")
    ]
    result = await repo.upsert_many(adv_data_list)
    assert len(result) == 2
    assert {str(adv.advertiser_id) for adv in result} == {str(adv_ids[0]), str(adv_ids[1])}