import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status
from src.backend.cache import redis_client

# Тест для проверки эндпоинтов клиента:
# - получение несуществующего клиента,
# - создание клиента и его последующее получение.
@pytest.mark.asyncio
async def test_client_endpoints(client: AsyncClient):
    # Пытаемся получить клиента, которого нет (ожидаем ошибку 404).
    non_existent_client = str(uuid4())
    get_client_response = await client.get(f"/clients/{non_existent_client}")
    assert get_client_response.status_code == 404

    # Создаём клиента.
    client_id = uuid4()
    client_payload = [{
        "client_id": str(client_id),
        "login": "clienttest",
        "age": 22,
        "location": "ClientCity",
        "gender": "MALE"
    }]
    post_response = await client.post("/clients/bulk", json=client_payload)
    assert post_response.status_code == 201
    client_list = post_response.json()
    assert client_list[0]["client_id"] == str(client_id)

    # Получаем созданного клиента и проверяем корректность данных.
    get_response = await client.get(f"/clients/{client_id}")
    assert get_response.status_code == 200
    client_data = get_response.json()
    assert client_data["login"] == "clienttest"


# Тест: Если при записи клика клиент не найден, POST /ads/{ad_id}/click возвращает 404.
@pytest.mark.asyncio
async def test_click_client_not_found(client: AsyncClient):
    await redis_client.flushdb()
    fake_ad_id = str(uuid4())
    click_payload = {"client_id": str(uuid4())}
    response = await client.post(f"/ads/{fake_ad_id}/click", json=click_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Рекламное объявление не найдено"