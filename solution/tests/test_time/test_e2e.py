import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status
from src.backend.cache import redis_client


# Тест эндпоинта изменения времени.
@pytest.mark.asyncio
async def test_time_advance_endpoint(client: AsyncClient):
    # Корректное изменение времени.
    payload = {"current_date": 7}
    response = await client.post("/time/advance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["current_date"] == 7

    # Некорректное изменение времени (отрицательное значение) должно вернуть ошибку.
    invalid_payload = {"current_date": -1}
    invalid_response = await client.post("/time/advance", json=invalid_payload)
    assert invalid_response.status_code == 400