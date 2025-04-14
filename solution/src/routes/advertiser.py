from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from src.schemas.advertiser import AdvertiserUpsert, AdvertiserOut
from src.repositories.advertiser import AdvertiserRepository
from src.backend.database import get_session

router = APIRouter(prefix="/advertisers", tags=["Advertisers"])


@router.get("/{advertiserId}", response_model=AdvertiserOut)
async def read_advertiser(advertiserId: UUID, session: AsyncSession = Depends(get_session)):
    repo = AdvertiserRepository(session)
    advertiser = await repo.get_by_id(advertiserId)
    if not advertiser:
        raise HTTPException(status_code=404, detail="Рекламодатель не найден")
    return advertiser

@router.post("/bulk", response_model=List[AdvertiserOut], status_code=201)
async def upsert_advertisers(advertisers: List[AdvertiserUpsert], session: AsyncSession = Depends(get_session)):
    repo = AdvertiserRepository(session)
    updated_advertisers = await repo.upsert_many(advertisers)
    return updated_advertisers
