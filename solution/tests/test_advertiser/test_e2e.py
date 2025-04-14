import pytest
from uuid import uuid4
from httpx import AsyncClient
from fastapi import status

# Тест для проверки получения несуществующего рекламодателя (ожидается ошибка 404).
@pytest.mark.asyncio
async def test_get_nonexistent_advertiser(client: AsyncClient):
    non_existent_id = str(uuid4())
    response = await client.get(f"/advertisers/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    # Исправлено: ожидаем сообщение об отсутствии рекламодателя.
    assert data["detail"] == "Рекламодатель не найден"

# Тест для получения кампании по ID, когда она не существует и рекламодатель.
@pytest.mark.asyncio
async def test_get_campaign_not_found_and_advertiser(client: AsyncClient):
    advertiser_id = str(uuid4())
    fake_campaign_id = str(uuid4())
    response = await client.get(f"/advertisers/{advertiser_id}/campaigns/{fake_campaign_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Рекламодатель не найден"