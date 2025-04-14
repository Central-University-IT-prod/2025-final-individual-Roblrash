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

# Тест для проверки создания кампании и её обновления через репозиторий.
@pytest.mark.asyncio
async def test_campaign_repository_create_and_update(session):
    # Устанавливаем начальное состояние
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")

    # Создаем рекламодателя
    adv_repo = AdvertiserRepository(session)
    adv_id = uuid4()
    adv_data = AdvertiserUpsert(advertiser_id=adv_id, name="Campaign Advertiser")
    await adv_repo.upsert(adv_data)

    # Создаем кампанию для рекламодателя
    camp_repo = CampaignRepository(session)
    targeting = Targeting(gender="MALE", age_from=20, age_to=40, location="Test City")
    camp_create = CampaignCreate(
        impressions_limit=100,
        clicks_limit=10,
        cost_per_impression=0.05,
        cost_per_click=0.2,
        ad_title="Test Ad",
        ad_text="Buy now!",
        start_date=1,
        end_date=10,
        targeting=targeting
    )
    campaign = await camp_repo.create_campaign(adv_id, camp_create)
    # Обновляем объект из сессии, чтобы убедиться, что данные актуальны
    await session.refresh(campaign)
    assert campaign.ad_title == "Test Ad"

    # Обновляем кампанию: изменяем cost_per_impression, cost_per_click, ad_title и start_date
    update_data = CampaignUpdate(
        impressions_limit=200,
        clicks_limit=20,
        cost_per_impression=0.06,
        cost_per_click=0.4,
        ad_title="Updated Ad",
        ad_text="Buy NOW!",
        start_date=5,  # Это новое значение для start_date
        end_date=10,
        targeting=targeting
    )
    updated_campaign = await camp_repo.update_campaign(adv_id, campaign.campaign_id, update_data)
    # Обновляем объект после commit
    await session.refresh(updated_campaign)
    # Проверяем, что обновленные поля соответствуют новым значениям
    assert float(updated_campaign.cost_per_impression) == 0.06
    assert updated_campaign.ad_title == "Updated Ad"

# Тест для проверки логирования показов (импрессий) и кликов через репозиторий кампаний.
@pytest.mark.asyncio
async def test_campaign_log_impression_and_click(session, test_redis):
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    targeting = Targeting(gender="ALL")
    camp_create = CampaignCreate(
        impressions_limit=50,
        clicks_limit=5,
        cost_per_impression=0.1,
        cost_per_click=0.5,
        ad_title="Redis Test Ad",
        ad_text="Test",
        start_date=0,
        end_date=5,
        targeting=targeting
    )
    campaign = await camp_repo.create_campaign(advertiser_id, camp_create)

    client_id = uuid4()
    # Логируем показ для клиента (должен учитываться только один раз).
    impressions_count = await camp_repo.log_impression(campaign.campaign_id, client_id, test_redis)
    assert impressions_count == 1
    impressions_count = await camp_repo.log_impression(campaign.campaign_id, client_id, test_redis)
    assert impressions_count == 1

    # Логируем клик для клиента (также должен учитываться только один раз).
    clicks_count = await camp_repo.log_click(campaign.campaign_id, client_id, test_redis)
    assert clicks_count == 1
    clicks_count = await camp_repo.log_click(campaign.campaign_id, client_id, test_redis)
    assert clicks_count == 1

# Тест для проверки постраничного вывода (пагинации) кампаний.
@pytest.mark.asyncio
async def test_campaign_pagination(session):
    from src.repositories.advertiser import AdvertiserRepository
    adv_repo = AdvertiserRepository(session)
    advertiser_id = uuid4()
    await adv_repo.upsert(AdvertiserUpsert(advertiser_id=advertiser_id, name="Pagination Advertiser"))

    camp_repo = CampaignRepository(session)
    targeting = Targeting(gender="ALL")
    # Создаем 15 кампаний для тестирования пагинации.
    for i in range(15):
        camp_create = CampaignCreate(
            impressions_limit=100,
            clicks_limit=10,
            cost_per_impression=0.1,
            cost_per_click=0.5,
            ad_title=f"Campaign {i}",
            ad_text="Pagination test",
            start_date=0,
            end_date=10,
            targeting=targeting
        )
        await camp_repo.create_campaign(advertiser_id, camp_create)

    page1 = await camp_repo.list_all_campaigns(advertiser_id, page=1, size=10)
    assert len(page1) == 10
    page2 = await camp_repo.list_all_campaigns(advertiser_id, page=2, size=10)
    assert len(page2) == 5

# Тест для проверки обновления несуществующей кампании: должна вернуть None.
@pytest.mark.asyncio
async def test_update_nonexistent_campaign(session):
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    fake_campaign_id = uuid4()
    update_data = CampaignUpdate(
        impressions_limit=200,
        clicks_limit=20,
        cost_per_impression=0.06,
        cost_per_click=0.4,
        ad_title="Updated Ad",
        ad_text="Buy NOW!",
        start_date=5,
        end_date=10,
        targeting={}
    )
    updated_campaign = await camp_repo.update_campaign(advertiser_id, fake_campaign_id, update_data)
    assert updated_campaign is None

# Тест для проверки удаления несуществующей кампании: должна вернуть False.
@pytest.mark.asyncio
async def test_delete_nonexistent_campaign(session):
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    fake_campaign_id = uuid4()
    deleted = await camp_repo.delete_campaign(advertiser_id, fake_campaign_id)
    assert deleted is False

# Тест для проверки получения кампании по ID, когда кампания не существует.
@pytest.mark.asyncio
async def test_get_campaign_by_id_nonexistent(session):
    camp_repo = CampaignRepository(session)
    advertiser_id = uuid4()
    fake_campaign_id = uuid4()
    campaign = await camp_repo.get_campaign_by_id(advertiser_id, fake_campaign_id)
    assert campaign is None