import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status
from src.backend.cache import redis_client

# Тест для CRUD-операций кампании (создание, получение, обновление, удаление).
@pytest.mark.asyncio
async def test_campaign_crud_endpoints(client: AsyncClient):
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")
    # Создаём рекламодателя.
    advertiser_id = uuid4()
    adv_payload = [{"advertiser_id": str(advertiser_id), "name": "CRUD Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == 201

    # Создаём кампанию для рекламодателя.
    targeting = {"gender": "ALL"}
    camp_payload = {
        "impressions_limit": 200,
        "clicks_limit": 20,
        "cost_per_impression": 0.2,
        "cost_per_click": 0.6,
        "ad_title": "CRUD Campaign Ad",
        "ad_text": "Try CRUD now!",
        "start_date": 5,
        "end_date": 15,
        "targeting": targeting
    }
    camp_response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=camp_payload)
    assert camp_response.status_code == 201
    campaign = camp_response.json()
    campaign_id = campaign["campaign_id"]

    # Получаем кампанию по её ID.
    get_response = await client.get(f"/advertisers/{advertiser_id}/campaigns/{campaign_id}")
    assert get_response.status_code == 200
    fetched_campaign = get_response.json()
    assert fetched_campaign["ad_title"] == "CRUD Campaign Ad"

    # Обновляем параметры кампании.
    update_payload = {"impressions_limit": 200, "clicks_limit": 20,"cost_per_impression": 0.25, "cost_per_click": 1,
                      "ad_title": "Updated CRUD Ad", "ad_text": "string", "start_date": 0, "end_date": 10, "targeting": {}}
    update_response = await client.put(f"/advertisers/{advertiser_id}/campaigns/{campaign_id}", json=update_payload)
    assert update_response.status_code == 200
    updated_campaign = update_response.json()
    assert updated_campaign["cost_per_impression"] == 0.25
    assert updated_campaign["ad_title"] == "Updated CRUD Ad"

    # Удаляем кампанию.
    delete_response = await client.delete(f"/advertisers/{advertiser_id}/campaigns/{campaign_id}")
    assert delete_response.status_code == 204

    # Проверяем, что после удаления кампания недоступна (ожидается ошибка 404).
    get_deleted_response = await client.get(f"/advertisers/{advertiser_id}/campaigns/{campaign_id}")
    assert get_deleted_response.status_code == 404

# Тест для случая, когда ни одна кампания не подходит клиенту.
@pytest.mark.asyncio
async def test_ads_no_matching_campaign(client: AsyncClient):
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")
    # Создаём рекламодателя.
    advertiser_id = uuid4()
    adv_payload = [{"advertiser_id": str(advertiser_id), "name": "Mismatch Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == 201

    # Создаём кампанию с таргетингом, который не совпадает с параметрами клиента.
    camp_payload = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "Mismatch Campaign",
        "ad_text": "No match!",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "FEMALE", "age_from": 20, "age_to": 30, "location": "Nowhere"}
    }
    camp_response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=camp_payload)
    assert camp_response.status_code == 201

    # Создаём клиента, для которого таргетинг не совпадает с кампанией.
    client_id = str(uuid4())
    client_payload = [{
        "client_id": client_id,
        "login": "nomatch",
        "age": 35,
        "location": "Somewhere",
        "gender": "MALE"
    }]
    cl_response = await client.post("/clients/bulk", json=client_payload)
    assert cl_response.status_code == 201

    # Устанавливаем текущее время.
    time_payload = {"current_date": 5}
    await client.post("/time/advance", json=time_payload)

    response = await client.get(f"/ads?client_id={client_id}")
    # Ожидаем 404, если нет подходящих кампаний.
    assert response.status_code == status.HTTP_404_NOT_FOUND or (
        response.status_code == status.HTTP_200_OK and response.json().get("detail") == "Не найдено подходящих под параметры компаний"
    )

# Тест для создания кампании с неверными данными (например, end_date < start_date).
@pytest.mark.asyncio
async def test_create_campaign_invalid(client: AsyncClient):
    # Создаём рекламодателя.
    await redis_client.set("current_day", 0)
    advertiser_id = str(uuid4())
    adv_payload = [{"advertiser_id": advertiser_id, "name": "Invalid Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == status.HTTP_201_CREATED

    # Попытка создать кампанию с некорректными данными.
    campaign_payload = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "Invalid Campaign",
        "ad_text": "This should fail",
        "start_date": 10,
        "end_date": 5,  # неверное значение
        "targeting": {"gender": "ALL"}
    }
    response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Ошибка валидации" in data["detail"]

# Тест для получения списка кампаний.
@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient):
    # Создаём рекламодателя.
    await redis_client.set("current_day", 0)
    advertiser_id = str(uuid4())
    adv_payload = [{"advertiser_id": advertiser_id, "name": "List Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == status.HTTP_201_CREATED

    # Создаём две кампании.
    campaign_payload1 = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "Campaign 1",
        "ad_text": "Test campaign 1",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "ALL"}
    }
    campaign_payload2 = {
        "impressions_limit": 200,
        "clicks_limit": 20,
        "cost_per_impression": 0.2,
        "cost_per_click": 1.0,
        "ad_title": "Campaign 2",
        "ad_text": "Test campaign 2",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "ALL"}
    }
    resp1 = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload1)
    resp2 = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload2)
    assert resp1.status_code == status.HTTP_201_CREATED
    assert resp2.status_code == status.HTTP_201_CREATED

    # Получаем список кампаний с пагинацией.
    response = await client.get(f"/advertisers/{advertiser_id}/campaigns?page=1&size=10")
    assert response.status_code == status.HTTP_200_OK
    campaigns = response.json()
    assert len(campaigns) >= 2

# Тест для обновления кампании, когда она не существует.
@pytest.mark.asyncio
async def test_update_campaign_not_found(client: AsyncClient):
    advertiser_id = str(uuid4())
    fake_campaign_id = str(uuid4())
    update_payload = {"impressions_limit": 200, "clicks_limit": 20,"cost_per_impression": 0.15, "cost_per_click": 1,
                      "ad_title": "Updated Ad", "ad_text": "string", "start_date": 0, "end_date": 10, "targeting": {"gender": "ALL"}}
    response = await client.put(f"/advertisers/{advertiser_id}/campaigns/{fake_campaign_id}", json=update_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Кампания или рекламодатель не найдены"


# Тест для обновления кампании с некорректными данными (ValueError).
@pytest.mark.asyncio
async def test_update_campaign_invalid(client: AsyncClient):
    await redis_client.set("current_day", 0)
    advertiser_id = str(uuid4())
    adv_payload = [{"advertiser_id": advertiser_id, "name": "Update Advertiser"}]
    adv_response = await client.post("/advertisers/bulk", json=adv_payload)
    assert adv_response.status_code == status.HTTP_201_CREATED

    # Создаём корректную кампанию.
    campaign_payload = {
        "impressions_limit": 100,
        "clicks_limit": 10,
        "cost_per_impression": 0.1,
        "cost_per_click": 0.5,
        "ad_title": "Campaign to Update",
        "ad_text": "Initial text",
        "start_date": 0,
        "end_date": 10,
        "targeting": {"gender": "ALL"}
    }
    camp_response = await client.post(f"/advertisers/{advertiser_id}/campaigns", json=campaign_payload)
    assert camp_response.status_code == status.HTTP_201_CREATED
    campaign = camp_response.json()
    campaign_id = campaign["campaign_id"]

    # Попытка обновить кампанию с некорректными данными (например, отрицательная цена).
    update_payload = {"cost_per_impression": -0.1, "ad_title": "Updated Title"}
    response = await client.put(f"/advertisers/{advertiser_id}/campaigns/{campaign_id}", json=update_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Ошибка валидации" in data["detail"]

# Тест для удаления кампании, когда она не существует.
@pytest.mark.asyncio
async def test_delete_campaign_not_found(client: AsyncClient):
    advertiser_id = str(uuid4())
    fake_campaign_id = str(uuid4())
    response = await client.delete(f"/advertisers/{advertiser_id}/campaigns/{fake_campaign_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Кампания или рекламодатель не найдены"