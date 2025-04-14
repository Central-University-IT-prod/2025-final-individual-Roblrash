import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status
from src.backend.cache import redis_client

# Тест: создание сущностей (рекламодателя, клиента, кампании), установка времени,
# получение рекламы, клик по рекламе и получение статистики кампании.
@pytest.mark.asyncio
async def test_e2e_create_entities_and_get_ad(client: AsyncClient):
    # Создаём рекламодателя с уникальным идентификатором.
    advertiser_id = uuid4()
    await redis_client.set("current_day", 0)
    advertiser_payload = [{"advertiser_id": str(advertiser_id), "name": "E2E Advertiser"}]
    response = await client.post("/advertisers/bulk", json=advertiser_payload)
    assert response.status_code == 201
    advertisers = response.json()
    assert advertisers[0]["advertiser_id"] == str(advertiser_id)

    # Создаём клиента (пользователя) с уникальным идентификатором.
    client_id = uuid4()
    client_payload = [{
        "client_id": str(client_id),
        "login": "e2euser",
        "age": 28,
        "location": "Test",
        "gender": "MALE"
    }]
    response = await client.post("/clients/bulk", json=client_payload)
    assert response.status_code == 201
    clients_resp = response.json()
    assert clients_resp[0]["client_id"] == str(client_id)

    # Создаём кампанию для рекламодателя с таргетингом, подходящим для клиента.
    campaign_payload = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "E2E Campaign Ad",
        "ad_text": "Buy E2E!",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "MALE", "age_from": 18, "age_to": 35, "location": "Test"}
    }
    response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload)
    assert response.status_code == 201
    campaign = response.json()
    campaign_id = campaign["campaign_id"]

    # Устанавливаем текущее время (день) для приложения.
    time_payload = {"current_date": 5}
    response = await client.post("/time/advance", json=time_payload)
    assert response.status_code == 200
    time_resp = response.json()
    assert time_resp["current_date"] == 5

    # Запрашиваем рекламу для клиента (ожидается, что будет выбрана ранее созданная кампания).
    response = await client.get(f"/ads?client_id={client_id}")
    assert response.status_code == 200
    ad = response.json()
    assert ad["ad_id"] == campaign_id
    assert ad["ad_title"] == "E2E Campaign Ad"

    # Регистрируем клик по рекламе.
    click_payload = {"client_id": str(client_id)}
    response = await client.post(f"/ads/{campaign_id}/click", json=click_payload)
    assert response.status_code == 204

    # Получаем статистику кампании и убеждаемся, что импрессии и клики зарегистрированы.
    response = await client.get(f"/stats/campaigns/{campaign_id}")
    assert response.status_code == 200
    stats = response.json()
    assert stats["impressions_count"] >= 1
    assert stats["clicks_count"] >= 1

# Тест для успешного получения рекламы.
@pytest.mark.asyncio
async def test_ads_successful(client: AsyncClient):
    await redis_client.flushdb()
    # Создаём рекламодателя.
    await redis_client.set("current_day", 0)
    advertiser_id = str(uuid4())
    adv_payload = [{"advertiser_id": advertiser_id, "name": "Matching Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == status.HTTP_201_CREATED

    # Создаём клиента, соответствующего таргетингу.
    client_id = str(uuid4())
    client_payload = [{
        "client_id": client_id,
        "login": "matchuser",
        "age": 28,
        "location": "Test",
        "gender": "MALE"
    }]
    client_response = await client.post("/clients/bulk", json=client_payload)
    assert client_response.status_code == 201

    # Создаём кампанию, подходящую по таргетингу.
    campaign_payload = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "Matching Campaign Ad",
        "ad_text": "Buy now!",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "MALE", "age_from": 18, "age_to": 35, "location": "Test"}
    }
    camp_response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload)
    assert camp_response.status_code == status.HTTP_201_CREATED
    campaign = camp_response.json()
    expected_ad_title = campaign["ad_title"]
    expected_ad_text = campaign["ad_text"]

    # Устанавливаем текущее время.
    time_payload = {"current_date": 5}
    time_response = await client.post("/time/advance", json=time_payload)
    assert time_response.status_code == status.HTTP_200_OK

    response = await client.get(f"/ads?client_id={client_id}")
    assert response.status_code == status.HTTP_200_OK
    ad = response.json()
    assert ad["ad_title"] == expected_ad_title
    assert ad["ad_text"] == expected_ad_text
    assert ad["advertiser_id"]  # поле не должно быть пустым

# Тест: Успешная запись клика.
@pytest.mark.asyncio
async def test_click_successful(client: AsyncClient):
    await redis_client.flushdb()
    # Создаём рекламодателя.
    await redis_client.set("current_day", 0)
    advertiser_id = str(uuid4())
    adv_payload = [{"advertiser_id": advertiser_id, "name": "Click Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == status.HTTP_201_CREATED

    # Создаём кампанию.
    campaign_payload = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "Click Campaign Ad",
        "ad_text": "Click now!",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "MALE", "age_from": 18, "age_to": 35, "location": "Test"}
    }
    camp_response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload)
    assert camp_response.status_code == status.HTTP_201_CREATED
    campaign = camp_response.json()
    ad_id = campaign["campaign_id"]

    # Создаём клиента.
    client_id = str(uuid4())
    client_payload = [{
        "client_id": client_id,
        "login": "clickuser",
        "age": 28,
        "location": "Test",
        "gender": "MALE"
    }]
    cl_response = await client.post("/clients/bulk", json=client_payload)
    assert cl_response.status_code == 201

    # Записываем клик.
    click_payload = {"client_id": client_id}
    response = await client.post(f"/ads/{ad_id}/click", json=click_payload)
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.asyncio
async def test_get_ad_with_ml_score(client: AsyncClient, session):
    from src.repositories.ml_score import MLScoreRepository
    from src.schemas.ml_score import MLScore
    # Устанавливаем текущий день и отключаем модерацию.
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")

    # Создаем рекламодателя.
    advertiser_id = str(uuid4())
    adv_payload = [{"advertiser_id": advertiser_id, "name": "Test Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == status.HTTP_201_CREATED

    # Создаем две кампании для рекламодателя с полным таргетингом,
    # чтобы точно совпадали с данными клиента.
    targeting = {
        "gender": "ALL",
    }
    # Цена за показ (0.6 + 1.0 = 1.5)
    camp_payload1 = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.5,
        "cost_per_click": 1.0,
        "ad_title": "Campaign 1",
        "ad_text": "Ad Text 1",
        "start_date": 0,
        "end_date": 10,
        "targeting": targeting
    }
    # Для Campaign 2 делаем чуть более выгодной цену за показ (0.6 + 1.0 = 1.6)
    camp_payload2 = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.6,
        "cost_per_click": 1.0,
        "ad_title": "Campaign 2",
        "ad_text": "Ad Text 2",
        "start_date": 0,
        "end_date": 10,
        "targeting": targeting
    }

    camp_response1 = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=camp_payload1)
    camp_response2 = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=camp_payload2)
    assert camp_response1.status_code == status.HTTP_201_CREATED
    assert camp_response2.status_code == status.HTTP_201_CREATED

    # Создаем клиента, который будет использоваться для показа рекламы.
    test_client_id = str(uuid4())
    client_payload = [{
        "client_id": test_client_id,
        "login": "ml_e2e_user",
        "age": 28,
        "location": "Test",
        "gender": "MALE"
    }]
    cl_response = await client.post("/clients/bulk", json=client_payload)
    assert cl_response.status_code == 201

    # Устанавливаем ML-скор для комбинации (test_client_id, advertiser_id) через MLScoreRepository.
    ml_repo = MLScoreRepository(session)
    # Сначала устанавливаем ML-скор равным 50, затем обновляем до 100.
    ml_data_initial = MLScore(client_id=test_client_id, advertiser_id=advertiser_id, score=50)
    await ml_repo.upsert(ml_data_initial)
    ml_data_updated = MLScore(client_id=test_client_id, advertiser_id=advertiser_id, score=100)
    await ml_repo.upsert(ml_data_updated)

    # Вызываем endpoint показа рекламы для test_client_id.
    get_ad_response = await client.get(f"/ads?client_id={test_client_id}")
    assert get_ad_response.status_code == status.HTTP_200_OK
    ad = get_ad_response.json()

    # Ожидаем, что будет выбрана кампания с более высокой прибылью/ML-оценкой, то есть "Campaign 2".
    assert ad["ad_title"] == "Campaign 2"

@pytest.mark.asyncio
async def test_get_ad_among_different_advertisers(client: AsyncClient, session):
    # Устанавливаем текущий день и отключаем модерацию.
    from src.repositories.ml_score import MLScoreRepository
    from src.schemas.ml_score import MLScore
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")

    # Создаем два рекламодателя.
    advertiser_id_1 = str(uuid4())
    advertiser_id_2 = str(uuid4())
    adv_payload1 = [{"advertiser_id": advertiser_id_1, "name": "Advertiser 1"}]
    adv_payload2 = [{"advertiser_id": advertiser_id_2, "name": "Advertiser 2"}]
    adv_response1 = await client.post("/advertisers/bulk", json=adv_payload1)
    adv_response2 = await client.post("/advertisers/bulk", json=adv_payload2)
    assert adv_response1.status_code == status.HTTP_201_CREATED
    assert adv_response2.status_code == status.HTTP_201_CREATED

    # Определяем targeting так, чтобы он точно совпадал с данными клиента.
    targeting = {
        "gender": "MALE",
        "age_from": 18,
        "age_to": 35,
        "location": "Test"
    }
    # Создаем кампанию для первого рекламодателя
    camp_payload1 = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.5,
        "cost_per_click": 1.0,
        "ad_title": "Campaign A1",
        "ad_text": "Ad Text A1",
        "start_date": 0,
        "end_date": 10,
        "targeting": targeting
    }
    # Создаем кампанию для второго рекламодателя
    camp_payload2 = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.5,
        "cost_per_click": 1.0,
        "ad_title": "Campaign A2",
        "ad_text": "Ad Text A2",
        "start_date": 0,
        "end_date": 10,
        "targeting": targeting
    }

    camp_response1 = await client.post(f"/advertisers/{advertiser_id_1}/campaigns", json=camp_payload1)
    camp_response2 = await client.post(f"/advertisers/{advertiser_id_2}/campaigns", json=camp_payload2)
    assert camp_response1.status_code == status.HTTP_201_CREATED
    assert camp_response2.status_code == status.HTTP_201_CREATED

    # Извлекаем данные кампаний.
    campaign1 = camp_response1.json()
    campaign2 = camp_response2.json()

    # Создаем клиента, который будет использоваться для показа рекламы.
    test_client_id = str(uuid4())
    client_payload = [{
        "client_id": test_client_id,
        "login": "e2e_ml_user",
        "age": 28,
        "location": "Test",
        "gender": "MALE"
    }]
    cl_response = await client.post("/clients/bulk", json=client_payload)
    assert cl_response.status_code == 201

    # Устанавливаем ML-скор для комбинации (test_client_id, advertiser_id_1) равный 50,
    # а для комбинации (test_client_id, advertiser_id_2) равный 100.
    ml_repo = MLScoreRepository(session)
    ml_data1 = MLScore(client_id=test_client_id, advertiser_id=advertiser_id_1, score=50)
    ml_data2 = MLScore(client_id=test_client_id, advertiser_id=advertiser_id_2, score=100)
    await ml_repo.upsert(ml_data1)
    await ml_repo.upsert(ml_data2)

    # Вызываем endpoint показа рекламы для test_client_id.
    get_ad_response = await client.get(f"/ads?client_id={test_client_id}")
    assert get_ad_response.status_code == status.HTTP_200_OK
    ad = get_ad_response.json()

    # Ожидаем, что будет выбрана кампания с более высоким ML-скор (Campaign A2).
    assert ad["ad_title"] == "Campaign A2"