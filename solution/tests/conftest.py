import os
import redis.asyncio as redis_asyncio
import fakeredis.aioredis

def fake_from_url(*args, **kwargs):
    return fakeredis.aioredis.FakeRedis(decode_responses=True, db=1)

redis_asyncio.from_url = fake_from_url

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.backend.database import Base, get_session
from src.main import app as main_app
from httpx import AsyncClient, ASGITransport

DATABASE_TEST_URL = os.getenv("DATABASE_TEST_URL", "sqlite+aiosqlite:///:memory:")

test_engine = create_async_engine(DATABASE_TEST_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

async def override_get_session():
    async with TestSessionLocal() as session:
        yield session

main_app.dependency_overrides[get_session] = override_get_session

@pytest_asyncio.fixture(scope="session", autouse=True)
async def async_engine():
    yield test_engine
    await test_engine.dispose()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_db(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def test_redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True, db=1)
    await r.flushdb()
    yield r
    await r.flushdb()
    await r.aclose()

@pytest_asyncio.fixture(autouse=True)
async def override_redis(test_redis, monkeypatch):
    from src.backend import cache
    monkeypatch.setattr(cache, "redis_client", test_redis)

main_app.router.on_startup.clear()

@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=main_app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as ac:
        yield ac

@pytest_asyncio.fixture(autouse=True)
async def clear_db(session):
    yield
    for table in reversed(Base.metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()