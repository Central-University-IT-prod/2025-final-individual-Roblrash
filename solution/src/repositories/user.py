from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.models.user import User
from src.schemas.client import ClientUpsert

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, client_id: UUID) -> User:
        stmt = select(User).where(User.client_id == client_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert(self, client_data: ClientUpsert) -> User:
        user = await self.get_by_id(client_data.client_id)
        if user:
            user.login = client_data.login
            user.age = client_data.age
            user.location = client_data.location
            user.gender = client_data.gender
        else:
            user = User(**client_data.model_dump(by_alias=True))
            self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def upsert_many(self, clients: list[ClientUpsert]) -> list[User]:
        results = []
        for client in clients:
            updated = await self.upsert(client)
            results.append(updated)
        return results
