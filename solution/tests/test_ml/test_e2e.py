import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status
from src.backend.cache import redis_client

# Тест для проверки работы эндпоинта ML-оценок.
@pytest.mark.asyncio
async def test_e2e_ml_score(client: AsyncClient):
    # Создаём рекламодателя.
    advertiser_id = uuid4()
    advertiser_payload = [{"advertiser_id": str(advertiser_id), "name": "ML Advertiser"}]
    response = await client.post("/advertisers/bulk", json=advertiser_payload)
    assert response.status_code == 201

    # Создаём клиента.
    client_id = uuid4()
    client_payload = [{
        "client_id": str(client_id),
        "login": "ml_e2e",
        "age": 30,
        "location": "Test",
        "gender": "FEMALE"
    }]
    response = await client.post("/clients/bulk", json=client_payload)
    assert response.status_code == 201

    # Отправляем ML-оценку для комбинации клиента и рекламодателя.
    ml_payload = {
        "client_id": str(client_id),
        "advertiser_id": str(advertiser_id),
        "score": 90
    }
    response = await client.post("/ml-scores/", json=ml_payload)
    assert response.status_code == 200
    ml_resp = response.json()
    assert ml_resp["score"] == 90