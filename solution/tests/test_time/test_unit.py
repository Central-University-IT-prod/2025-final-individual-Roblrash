import pytest
from fastapi import status
from src.backend.cache import redis_client

@pytest.mark.asyncio
async def test_advance_time_success_no_current_day(client, test_redis):
    """
    Тест успешного обновления времени, когда ключ 'current_day' отсутствует (значение по умолчанию считается 0).
    Отправляем новый current_date (например, 5) – должен вернуться успешный ответ с current_date=5.
    """
    await redis_client.set("current_day", 0)
    payload = {"current_date": 5}
    response = await client.post("/time/advance", json=payload)
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["current_date"] == 5

@pytest.mark.asyncio
async def test_advance_time_success_with_current_day(client, test_redis):
    """
    Тест успешного обновления времени, когда в redis уже установлен current_day и новое значение больше текущего.
    """
    # Устанавливаем текущее значение равным 10
    await redis_client.set("current_day", 10)
    payload = {"current_date": 15}
    response = await client.post("/time/advance", json=payload)
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["current_date"] == 15

@pytest.mark.asyncio
async def test_advance_time_bad_request_lower_date(client, test_redis):
    """
    Тест, когда новое значение current_date меньше текущего (например, 5 при current_day=10).
    Ожидается ошибка 400 с соответствующим сообщением.
    """
    await redis_client.set("current_day", 10)
    payload = {"current_date": 5}
    response = await client.post("/time/advance", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    expected_detail = "Нельзя установить день меньше текущего (10)"
    assert data["detail"] == expected_detail
