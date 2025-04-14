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

# Тест для проверки агрегирования статистики по кампании: подсчет импрессий, кликов и расходов.
@pytest.mark.asyncio
async def test_campaign_stats_functions(session, test_redis):
    await redis_client.set("current_day", 0)
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    targeting = Targeting(gender="ALL")
    camp_create = CampaignCreate(
        impressions_limit=20,
        clicks_limit=5,
        cost_per_impression=0.2,
        cost_per_click=1.0,
        ad_title="Stats Unit Test Ad",
        ad_text="Stats unit",
        start_date=0,
        end_date=5,
        targeting=targeting
    )
    campaign = await camp_repo.create_campaign(advertiser_id, camp_create)
    campaign_id = campaign.campaign_id

    # Логируем показ и клик для нескольких клиентов.
    client_ids = [uuid4() for _ in range(3)]
    for cid in client_ids:
        await camp_repo.log_impression(campaign_id, cid, test_redis)
        await camp_repo.log_click(campaign_id, cid, test_redis)

    stats = await camp_repo.get_campaign_stats(campaign_id, test_redis)
    assert stats["impressions_count"] == 3
    assert stats["clicks_count"] == 3
    assert stats["spent_impressions"] > 0
    assert stats["spent_clicks"] > 0
    assert stats["spent_total"] == stats["spent_impressions"] + stats["spent_clicks"]

# Тест для проверки получения ежедневной статистики кампании.
@pytest.mark.asyncio
async def test_campaign_daily_stats(session, test_redis):
    await redis_client.set("current_day", 0)
    from src.repositories.campaign import CampaignRepository
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    targeting = Targeting(gender="ALL")
    camp_create = CampaignCreate(
        impressions_limit=20,
        clicks_limit=5,
        cost_per_impression=0.2,
        cost_per_click=1.0,
        ad_title="Daily Stats Ad",
        ad_text="Daily stats",
        start_date=0,
        end_date=5,
        targeting=targeting
    )
    campaign = await camp_repo.create_campaign(advertiser_id, camp_create)
    campaign_id = campaign.campaign_id

    # Устанавливаем текущий день в Redis (в виде строки).
    await test_redis.set("current_day", "3")
    # Симулируем импрессии и клики в разные дни.
    day1_key = f"campaign:{campaign_id}:daily:impressions:1"
    await test_redis.sadd(day1_key, str(uuid4()))
    day2_key = f"campaign:{campaign_id}:daily:clicks:2"
    await test_redis.sadd(day2_key, str(uuid4()))

    daily_stats = await camp_repo.get_campaign_daily_stats(campaign_id, test_redis)
    # Если кампания с start_date=0 и текущим днем=3, ожидается 4 дня: 0,1,2,3.
    assert len(daily_stats) == 4
    non_zero = any(stat["impressions_count"] > 0 or stat["clicks_count"] > 0 for stat in daily_stats)
    assert non_zero

# Тест для кампании, которая уже закончилась: ежедневная статистика должна возвращать данные только до end_date.
@pytest.mark.asyncio
async def test_campaign_daily_stats_with_finished_campaign(session, test_redis):
    await redis_client.set("current_day", 0)
    from src.repositories.campaign import CampaignRepository
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    # Кампания с end_date=3, текущий день будем задавать как "5".
    camp_create = CampaignCreate(
        impressions_limit=100,
        clicks_limit=10,
        cost_per_impression=0.1,
        cost_per_click=0.5,
        ad_title="Finished Campaign",
        ad_text="Test finished campaign",
        start_date=0,
        end_date=3,
        targeting=Targeting(gender="ALL")
    )
    campaign = await camp_repo.create_campaign(advertiser_id, camp_create)
    campaign_id = campaign.campaign_id
    await test_redis.set("current_day", "5")
    daily_stats = await camp_repo.get_campaign_daily_stats(campaign_id, test_redis)
    # Ожидаем, что статистика собрана по дням: 0,1,2,3.
    assert len(daily_stats) == 4
    assert daily_stats[-1]["date"] == 3

# Тест для активной кампании: ежедневная статистика должна возвращать данные до текущего дня.
@pytest.mark.asyncio
async def test_campaign_daily_stats_with_active_campaign(session, test_redis):
    await redis_client.set("current_day", 0)
    from src.repositories.campaign import CampaignRepository
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    # Кампания с end_date=10, текущий день "5".
    camp_create = CampaignCreate(
        impressions_limit=100,
        clicks_limit=10,
        cost_per_impression=0.1,
        cost_per_click=0.5,
        ad_title="Active Campaign",
        ad_text="Test active campaign",
        start_date=0,
        end_date=10,
        targeting=Targeting(gender="ALL")
    )
    campaign = await camp_repo.create_campaign(advertiser_id, camp_create)
    campaign_id = campaign.campaign_id
    await test_redis.set("current_day", "5")
    daily_stats = await camp_repo.get_campaign_daily_stats(campaign_id, test_redis)
    # Ожидаем, что статистика собрана для дней 0-5 (всего 6 дней).
    assert len(daily_stats) == 6
    assert daily_stats[-1]["date"] == 5

# Тест для проверки агрегированной статистики рекламодателя, когда рекламодатель не существует.
@pytest.mark.asyncio
async def test_advertiser_stats_no_campaigns(session, test_redis):
    stats = await CampaignRepository(session).get_advertiser_stats(uuid4(), test_redis)
    assert stats is None

# Тест для проверки ежедневной статистики рекламодателя, когда рекламодатель не существует.
@pytest.mark.asyncio
async def test_advertiser_daily_stats_no_campaigns(session, test_redis):
    daily_stats = await CampaignRepository(session).get_advertiser_daily_stats(uuid4(), test_redis)
    assert daily_stats is None
