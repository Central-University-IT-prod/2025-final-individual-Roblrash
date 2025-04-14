import asyncio
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from src.backend.database import get_session
from minio.error import S3Error
from src.repositories.campaign import CampaignRepository
from src.repositories.user import UserRepository
from src.repositories.ml_score import MLScoreRepository
from src.backend.cache import redis_client
from src.schemas.ads import Ad, ClickRequest
from src.services.ad_matching import campaign_matches_client
from src.services.image_service import save_image_file, delete_image_file, extract_object_info, get_minio_client
from src.backend.metrics import api_errors_total

router = APIRouter(prefix="/ads", tags=["Ads"])


@router.get("", response_model=Ad)
async def get_ad(
    client_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session)
):
    current_day_str = await redis_client.get("current_day")
    current_day = int(current_day_str) if current_day_str is not None else 0

    user_repo = UserRepository(session)
    client = await user_repo.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")

    campaign_repo = CampaignRepository(session)
    active_campaigns = await campaign_repo.list_active_campaigns(current_day)
    if not active_campaigns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено активных кампаний")

    candidate_campaigns = [camp for camp in active_campaigns if campaign_matches_client(camp.targeting, client)]
    if not candidate_campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдено подходящих под параметры кампаний"
        )

    ml_repo = MLScoreRepository(session)

    campaign_metrics = []
    incomes = []
    ctrs = []

    for campaign in candidate_campaigns:
        ml_task = ml_repo.get_by_ids(client_id, campaign.advertiser_id)
        imp_task = campaign_repo.get_impressions_count(campaign.campaign_id, redis_client)
        click_task = campaign_repo.get_clicks_count(campaign.campaign_id, redis_client)
        ml_result, imp_count, click_count = await asyncio.gather(
            ml_task, imp_task, click_task, return_exceptions=True
        )

        ml_value = ml_result.score if (ml_result and not isinstance(ml_result, Exception)) else 0
        ctr = (click_count / imp_count) if imp_count > 0 else 0

        new_income = Decimal(str(ml_value)) * Decimal(str(campaign.cost_per_click)) + Decimal(str(campaign.cost_per_impression))
        incomes.append(new_income)
        ctr_decimal = Decimal(str(ctr))
        ctrs.append(ctr_decimal)

        campaign_metrics.append({
            "campaign": campaign,
            "ml_value": ml_value,
            "ctr": ctr,
            "new_income": new_income,
            "impressions_limit": campaign.impressions_limit,
            "impressions_count": imp_count
        })

    max_income = max(incomes) if incomes else Decimal("1")
    max_ctr = max(ctrs) if ctrs else Decimal("1")

    best_campaign = None
    best_score = -float("inf")

    for metrics in campaign_metrics:
        if (metrics["impressions_count"] + 1) >= (metrics["impressions_limit"] * 1.05):
            continue

        normalized_income = metrics["new_income"] / max_income if max_income > 0 else metrics["new_income"]
        normalized_ctr = Decimal(str(metrics["ctr"])) / max_ctr if max_ctr > 0 else Decimal(str(metrics["ctr"]))
        candidate_score = Decimal("0.8") * normalized_income + Decimal("0.2") * normalized_ctr
        candidate_score = float(candidate_score)

        if candidate_score > best_score:
            best_score = candidate_score
            best_campaign = metrics["campaign"]

    if not best_campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не выбрана")

    await campaign_repo.log_impression(best_campaign.campaign_id, client_id, redis_client)

    return Ad(
        ad_id=best_campaign.campaign_id,
        ad_title=best_campaign.ad_title,
        ad_text=best_campaign.ad_text,
        advertiser_id=best_campaign.advertiser_id,
        image_url=getattr(best_campaign, "image_url", None)
    )



@router.post("/{ad_id}/upload-image", status_code=status.HTTP_200_OK)
async def upload_ad_image(ad_id: UUID, file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    """
    Загружает изображение для рекламного объявления и обновляет запись кампании.
    Если изображение уже загружено, возвращает существующий URL.
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат изображения")

    campaign_repo = CampaignRepository(session)
    campaign = await campaign_repo.get_campaign_by_id_only(ad_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламное объявление не найдено")

    if campaign.image_url is not None:
        return {"ad_id": ad_id, "image_url": campaign.image_url}

    image_url = await save_image_file(file)
    campaign.image_url = image_url
    await session.commit()
    await session.refresh(campaign)
    return {"ad_id": ad_id, "image_url": image_url}


@router.put("/{ad_id}/update-image", status_code=status.HTTP_200_OK)
async def update_ad_image(ad_id: UUID, file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    """
    Обновляет изображение рекламного объявления: если изображение уже есть, оно удаляется, а затем загружается новое.
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат изображения")

    campaign_repo = CampaignRepository(session)
    campaign = await campaign_repo.get_campaign_by_id_only(ad_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламное объявление не найдено")

    if getattr(campaign, "image_url", None):
        await delete_image_file(campaign.image_url)

    new_image_url = await save_image_file(file)
    campaign.image_url = new_image_url
    await session.commit()
    await session.refresh(campaign)
    return {"ad_id": ad_id, "image_url": new_image_url}


@router.delete("/{ad_id}/delete-image", status_code=status.HTTP_200_OK)
async def delete_ad_image(ad_id: UUID, session: AsyncSession = Depends(get_session)):
    """
    Удаляет изображение, связанное с рекламным объявлением, из MinIO и обновляет запись кампании.
    """
    campaign_repo = CampaignRepository(session)
    campaign = await campaign_repo.get_campaign_by_id_only(ad_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламное объявление не найдено")

    if not getattr(campaign, "image_url", None):
        raise HTTPException(status_code=400, detail="Изображение не установлено для данного объявления")

    await delete_image_file(campaign.image_url)
    campaign.image_url = None
    await session.commit()
    await session.refresh(campaign)
    return {"ad_id": ad_id, "message": "Изображение удалено"}


@router.get("/{ad_id}/image", status_code=status.HTTP_200_OK)
async def get_ad_image(ad_id: UUID, session: AsyncSession = Depends(get_session)):
    """
    Возвращает изображение для рекламного объявления по его идентификатору.
    Эндпоинт извлекает информацию о кампании из БД, получает из MinIO объект изображения
    и возвращает его в виде StreamingResponse.
    """
    campaign_repo = CampaignRepository(session)
    campaign = await campaign_repo.get_campaign_by_id_only(ad_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламное объявление не найдено")

    if not getattr(campaign, "image_url", None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Изображение не установлено для данного объявления")

    try:
        bucket, object_name = extract_object_info(campaign.image_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    client = get_minio_client()
    loop = asyncio.get_running_loop()

    def get_object():
        try:
            return client.get_object(bucket, object_name)
        except S3Error as err:
            api_errors_total.inc()
            raise HTTPException(status_code=500, detail=f"Ошибка при получении изображения: {err}")

    object_data = await loop.run_in_executor(None, get_object)

    ext = object_name.split(".")[-1].lower()
    if ext in ["jpg", "jpeg"]:
        media_type = "image/jpeg"
    elif ext == "png":
        media_type = "image/png"
    else:
        media_type = "application/octet-stream"

    return StreamingResponse(object_data, media_type=media_type)


@router.post("/{ad_id}/click", status_code=status.HTTP_204_NO_CONTENT)
async def record_click(ad_id: UUID, click: ClickRequest, session: AsyncSession = Depends(get_session)):
    campaign_repo = CampaignRepository(session)
    campaign = await campaign_repo.get_campaign_by_id_only(ad_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рекламное объявление не найдено")
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(click.client_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    campaign_repo = CampaignRepository(session)
    await campaign_repo.log_click(ad_id, click.client_id, redis_client)
    return None
