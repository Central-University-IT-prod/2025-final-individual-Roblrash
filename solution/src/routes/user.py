from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from src.schemas.client import ClientUpsert, ClientOut
from src.repositories.user import UserRepository
from src.backend.database import get_session

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/{clientId}", response_model=ClientOut)
async def read_client(clientId: UUID, session: AsyncSession = Depends(get_session)):
    repo = UserRepository(session)
    client = await repo.get_by_id(clientId)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client

@router.post("/bulk", response_model=List[ClientOut], status_code=201)
async def upsert_clients(clients: List[ClientUpsert], session: AsyncSession = Depends(get_session)):
    repo = UserRepository(session)
    updated_clients = await repo.upsert_many(clients)
    return updated_clients
