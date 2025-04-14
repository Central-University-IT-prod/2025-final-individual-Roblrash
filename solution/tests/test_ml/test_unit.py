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


# Тест для проверки работы репозитория ML‑оценок: вставка и получение оценки.
@pytest.mark.asyncio
async def test_ml_score_repository(session):
    user_repo = UserRepository(session)
    ml_repo = MLScoreRepository(session)
    client_id = uuid4()
    advertiser_id = uuid4()

    client_data = ClientUpsert(
        client_id=client_id,
        login="mluser",
        age=25,
        location="Test",
        gender="FEMALE"
    )
    await user_repo.upsert(client_data)

    ml_data = MLScore(client_id=client_id, advertiser_id=advertiser_id, score=85)
    ml_score_obj = await ml_repo.upsert(ml_data)
    assert ml_score_obj.score == 85

# Тест для проверки обновления ML‑оценки: вставка и последующее обновление.
@pytest.mark.asyncio
async def test_ml_score_update(session):
    user_repo = UserRepository(session)
    ml_repo = MLScoreRepository(session)
    client_id = uuid4()
    advertiser_id = uuid4()
    await user_repo.upsert(
        ClientUpsert(client_id=client_id, login="mlupdate", age=40, location="City", gender="FEMALE")
    )
    ml_data = MLScore(client_id=client_id, advertiser_id=advertiser_id, score=50)
    ml_score_obj = await ml_repo.upsert(ml_data)
    assert ml_score_obj.score == 50
    ml_data_updated = MLScore(client_id=client_id, advertiser_id=advertiser_id, score=75)
    ml_score_obj_updated = await ml_repo.upsert(ml_data_updated)
    assert ml_score_obj_updated.score == 75

# Тест для проверки расчета средней ML‑оценки после добавления нескольких значений.
@pytest.mark.asyncio
async def test_get_average_ml_score(session, test_redis):
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    targeting = Targeting(gender="ALL")
    camp_create = CampaignCreate(
        impressions_limit=100,
        clicks_limit=10,
        cost_per_impression=0.1,
        cost_per_click=0.5,
        ad_title="ML Score Ad",
        ad_text="ML score test",
        start_date=0,
        end_date=5,
        targeting=targeting
    )
    campaign = await camp_repo.create_campaign(advertiser_id, camp_create)
    campaign_id = campaign.campaign_id

    await camp_repo.log_ml_score(campaign_id, 80)
    await camp_repo.log_ml_score(campaign_id, 100)
    await camp_repo.log_ml_score(campaign_id, 90)

    await session.commit()

    avg_score = await camp_repo.get_average_ml_score(campaign_id)
    assert avg_score == 90.0