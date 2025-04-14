from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate
from src.repositories.campaign import CampaignRepository
from src.backend.database import get_session
from src.services.moderation import moderate_text, should_moderate
from src.repositories.advertiser import AdvertiserRepository

router = APIRouter(prefix="/advertisers/{advertiserId}/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    advertiserId: UUID,
    campaign: CampaignCreate,
    session: AsyncSession = Depends(get_session)
):
    advertiser_repo = AdvertiserRepository(session)
    advertiser = await advertiser_repo.get_by_id(advertiserId)
    if advertiser is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рекламодатель не найден"
        )

    if await should_moderate():
        mod_response_text = await moderate_text(campaign.ad_text)
        mod_response_title = await moderate_text(campaign.ad_title)

        if mod_response_text["results"][0]["flagged"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Рекламный текст не прошел модерацию"
            )
        if mod_response_title["results"][0]["flagged"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заголовок объявления не прошел модерацию"
            )

    repo = CampaignRepository(session)
    try:
        new_campaign = await repo.create_campaign(advertiserId, campaign)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return new_campaign

@router.get("", response_model=list[CampaignOut])
async def list_all_campaigns(
    advertiserId: UUID,
    page: int = Query(1, ge=1, description="Номер страницы (не меньше 1)"),
    size: int = Query(10, ge=0, description="Количество записей на странице от 0"),
    session: AsyncSession = Depends(get_session)
):
    advertiser_repo = AdvertiserRepository(session)
    advertiser = await advertiser_repo.get_by_id(advertiserId)
    if advertiser is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рекламодатель не найден"
        )
    repo = CampaignRepository(session)
    campaigns = await repo.list_all_campaigns(advertiserId, page, size)
    return campaigns


@router.get("/{campaignId}", response_model=CampaignOut)
async def get_campaign(
    advertiserId: UUID,
    campaignId: UUID,
    session: AsyncSession = Depends(get_session)
):
    advertiser_repo = AdvertiserRepository(session)
    advertiser = await advertiser_repo.get_by_id(advertiserId)
    if advertiser is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рекламодатель не найден"
        )
    repo = CampaignRepository(session)
    campaign = await repo.get_campaign_by_id(advertiserId, campaignId)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена")
    return campaign


@router.put("/{campaignId}", response_model=CampaignOut)
async def update_campaign(
    advertiserId: UUID,
    campaignId: UUID,
    update: CampaignUpdate,
    session: AsyncSession = Depends(get_session)
):
    if await should_moderate():
        if update.ad_text is not None:
            mod_response_text = await moderate_text(update.ad_text)
            if mod_response_text["results"][0]["flagged"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Обновленный рекламный текст не прошел модерацию"
                )
        if update.ad_title is not None:
            mod_response_title = await moderate_text(update.ad_title)
            if mod_response_title["results"][0]["flagged"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Обновленный заголовок объявления не прошел модерацию"
                )

    repo = CampaignRepository(session)
    try:
        updated_campaign = await repo.update_campaign(advertiserId, campaignId, update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    if not updated_campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кампания или рекламодатель не найдены"
        )
    return updated_campaign


@router.delete("/{campaignId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    advertiserId: UUID,
    campaignId: UUID,
    session: AsyncSession = Depends(get_session)
):
    repo = CampaignRepository(session)
    deleted = await repo.delete_campaign(advertiserId, campaignId)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Кампания или рекламодатель не найдены")
    return None
