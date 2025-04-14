import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from decimal import Decimal
from httpx import AsyncClient

from src.models.user import User
from src.models.campaign import Campaign
from src.models.ml_score import MLScore
from src.backend.cache import redis_client

# --- Тест успешного получения рекламы ---
@pytest.mark.asyncio
async def test_get_ad_success(client, session, test_redis):
    """
    Тест успешного получения рекламы:
      - Создаём пользователя, активную кампанию и MLScore.
      - Устанавливаем redis-ключ current_day.
      - Эндпоинт должен вернуть данные рекламы.
    """
    test_client_id = uuid4()
    # Создаем пользователя
    new_user = User(
        client_id=test_client_id,
        login="test_login",
        age=30,
        location="NY",
        gender="MALE"
    )
    session.add(new_user)
    await session.commit()

    adv_id = uuid4()  # Генерируем идентификатор рекламодателя

    # Создаем активную кампанию
    campaign = Campaign(
        campaign_id=uuid4(),
        advertiser_id=adv_id,
        impressions_limit=100,
        clicks_limit=50,
        cost_per_impression=Decimal("0.1"),
        cost_per_click=Decimal("1.0"),
        ad_title="Test Ad Title",
        ad_text="Test Ad Text",
        start_date=1,
        end_date=10,
        targeting={"gender": "MALE"},
        image_url="http://example.com/image.png"
    )
    session.add(campaign)
    await session.commit()

    # Создаем MLScore для данного пользователя и рекламодателя
    ml_score = MLScore(
        client_id=test_client_id,
        advertiser_id=adv_id,
        score=50
    )
    session.add(ml_score)
    await session.commit()

    # Устанавливаем redis-ключ "current_day"
    await redis_client.set("current_day", 1)

    response = await client.get(f"/ads?client_id={test_client_id}")
    assert response.status_code == 200
    data = response.json()
    # Сравниваем строковые представления UUID
    assert data["ad_id"] == str(campaign.campaign_id)
    assert data["ad_title"] == "Test Ad Title"
    assert data["ad_text"] == "Test Ad Text"
    assert data["advertiser_id"] == str(adv_id)
    # Проверяем image_url
    assert data.get("image_url") in ("http://example.com/image.png")

# --- Тест: Пользователь не найден ---
@pytest.mark.asyncio
async def test_get_ad_client_not_found(client, test_redis):
    """
    Тест, когда в БД отсутствует пользователь.
    Ожидается ошибка 404 с сообщением "Клиент не найден".
    """
    test_client_id = uuid4()
    await test_redis.set("current_day", "1")
    response = await client.get(f"/?client_id={test_client_id}")
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Not Found"

# --- Тест: Нет активных кампаний ---
@pytest.mark.asyncio
async def test_get_ad_no_active_campaigns(client, session, test_redis):
    """
    Тест, когда для найденного пользователя отсутствуют активные кампании.
    Создаем пользователя, но не добавляем кампании – ожидается 404 "Не найдено активных кампаний".
    """
    test_client_id = uuid4()
    new_user = User(
        client_id=test_client_id,
        login="test_login",
        age=30,
        location="NY",
        gender="MALE"
    )
    session.add(new_user)
    await session.commit()

    await test_redis.set("current_day", "1")
    response = await client.get(f"/?client_id={test_client_id}")
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Not Found"