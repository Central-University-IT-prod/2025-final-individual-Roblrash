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


# Тест для проверки создания/обновления клиента (пользователя) через репозиторий.
@pytest.mark.asyncio
async def test_user_repository(session):
    repo = UserRepository(session)
    client_id = uuid4()
    client_data = ClientUpsert(
        client_id=client_id,
        login="testuser",
        age=30,
        location="Test City",
        gender="MALE"
    )
    user = await repo.upsert(client_data)
    assert user.client_id == client_id
    assert user.login == "testuser"

# Тест для проверки bulk‑операции для клиентов.
@pytest.mark.asyncio
async def test_user_upsert_many(session):
    repo = UserRepository(session)
    client_ids = [uuid4(), uuid4()]
    clients_data = [
        ClientUpsert(client_id=client_ids[0], login="bulk1", age=21, location="City1", gender="FEMALE"),
        ClientUpsert(client_id=client_ids[1], login="bulk2", age=31, location="City2", gender="MALE")
    ]
    result = await repo.upsert_many(clients_data)
    assert len(result) == 2
    assert {str(u.client_id) for u in result} == {str(client_ids[0]), str(client_ids[1])}