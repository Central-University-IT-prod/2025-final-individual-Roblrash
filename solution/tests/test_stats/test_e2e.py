import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status
from src.backend.cache import redis_client

# Тест для проверки эндпоинтов статистики:
# - статистика по кампании,
# - статистика по рекламодателю,
# - ежедневная статистика.
@pytest.mark.asyncio
async def test_stats_endpoints(client: AsyncClient):
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")
    # Создаём рекламодателя.
    advertiser_id = uuid4()
    adv_payload = [{"advertiser_id": str(advertiser_id), "name": "Stats Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == 201

    # Создаём клиента.
    client_id = uuid4()
    client_payload = [{
        "client_id": str(client_id),
        "login": "statsuser",
        "age": 35,
        "location": "StatsCity",
        "gender": "FEMALE"
    }]
    cl_response = await client.post("/clients/bulk", json=client_payload)
    assert cl_response.status_code == 201

    # Создаём кампанию с таргетингом, подходящим для клиента.
    camp_payload = {
        "impressions_limit": 50,
        "clicks_limit": 5,
        "cost_per_impression": 0.3,
        "cost_per_click": 1.0,
        "ad_title": "Stats Campaign Ad",
        "ad_text": "Stats!",
        "start_date": 1,
        "end_date": 10,
        "targeting": {"gender": "FEMALE", "age_from": 30, "age_to": 40, "location": "StatsCity"}
    }
    camp_response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=camp_payload)
    assert camp_response.status_code == 201
    campaign = camp_response.json()
    campaign_id = campaign["campaign_id"]

    # Устанавливаем текущее время (день).
    time_payload = {"current_date": 5}
    time_response = await client.post("/time/advance", json=time_payload)
    assert time_response.status_code == 200

    # Запрашиваем рекламу (это приводит к логированию показа).
    ad_response = await client.get(f"/ads?client_id={client_id}")
    assert ad_response.status_code == 200

    # Получаем агрегированную статистику по кампании.
    stats_response = await client.get(f"/stats/campaigns/{campaign_id}")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["impressions_count"] >= 1

    # Получаем агрегированную статистику по рекламодателю (для всех кампаний).
    adv_stats_response = await client.get(f"/stats/advertisers/{advertiser_id}/campaigns")
    assert adv_stats_response.status_code == 200
    adv_stats_data = adv_stats_response.json()
    assert adv_stats_data["impressions_count"] >= stats_data["impressions_count"]

    # Получаем ежедневную статистику по кампании.
    daily_response = await client.get(f"/stats/campaigns/{campaign_id}/daily")
    assert daily_response.status_code == 200
    daily_stats = daily_response.json()
    assert isinstance(daily_stats, list)

    # Получаем ежедневную статистику по рекламодателю.
    daily_adv_response = await client.get(f"/stats/advertisers/{advertiser_id}/campaigns/daily")
    assert daily_adv_response.status_code == 200
    daily_adv_stats = daily_adv_response.json()
    assert isinstance(daily_adv_stats, list)