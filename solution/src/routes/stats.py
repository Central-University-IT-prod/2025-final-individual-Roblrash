from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.database import get_session
from src.repositories.campaign import CampaignRepository
from src.backend.cache import redis_client
from src.schemas.stats import Stats, DailyStats

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/campaigns/{campaignId}", response_model=Stats)
async def get_campaign_stats(campaignId: UUID, session: AsyncSession = Depends(get_session)):
    repo = CampaignRepository(session)
    stats = await repo.get_campaign_stats(campaignId, redis_client)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return stats

@router.get("/advertisers/{advertiserId}/campaigns", response_model=Stats)
async def get_advertiser_stats(advertiserId: UUID, session: AsyncSession = Depends(get_session)):
    repo = CampaignRepository(session)
    stats = await repo.get_advertiser_stats(advertiserId, redis_client)
    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламодатель не найден")
    return stats

@router.get("/campaigns/{campaignId}/daily", response_model=list[DailyStats])
async def get_campaign_daily_stats(campaignId: UUID, session: AsyncSession = Depends(get_session)):
    repo = CampaignRepository(session)
    daily_stats = await repo.get_campaign_daily_stats(campaignId, redis_client)
    if daily_stats is None or not daily_stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return daily_stats

@router.get("/advertisers/{advertiserId}/campaigns/daily", response_model=list[DailyStats])
async def get_advertiser_daily_stats(advertiserId: UUID, session: AsyncSession = Depends(get_session)):
    repo = CampaignRepository(session)
    daily_stats = await repo.get_advertiser_daily_stats(advertiserId, redis_client)
    if daily_stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламодатель не найден")
    return daily_stats
