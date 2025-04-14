from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError
from src.models.campaign import Campaign
from src.schemas.campaign import CampaignCreate, CampaignUpdate
from src.backend.cache import redis_client
from src.repositories.advertiser import AdvertiserRepository
from src.backend.metrics import (
    ad_clicks_total,
    ad_impressions_total,
    ad_impression_revenue,
    ad_click_revenue
)

async def validate_campaign_update(data: dict, current_day: int):
    update = CampaignUpdate(**data)
    if update.start_date < current_day:
        raise ValueError("День начала не может быть в прошлом")
    if update.end_date < current_day:
        raise ValueError("День окончания не может быть в прошлом")
    return update

class CampaignRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_campaign(self, advertiser_id: UUID, campaign_data: CampaignCreate) -> Campaign:
        stored_day = await redis_client.get("current_day")
        current_day = int(stored_day) if stored_day is not None else 0

        if campaign_data.start_date < current_day:
            raise ValueError("Дата начала не может быть в прошлом")
        if campaign_data.end_date < current_day:
            raise ValueError("Дата окончания не может быть в прошлом")
        if campaign_data.end_date < campaign_data.start_date:
            raise ValueError("Дата окончания не может быть раньше даты начала")

        if campaign_data.targeting:
            targeting_data = campaign_data.targeting.model_dump(exclude_unset=True)
            complete_targeting = {
                "gender": targeting_data.get("gender", None),
                "age_from": targeting_data.get("age_from", None),
                "age_to": targeting_data.get("age_to", None),
                "location": targeting_data.get("location", None)
            }
        else:
            complete_targeting = {
                "gender": None,
                "age_from": None,
                "age_to": None,
                "location": None
            }

        new_campaign = Campaign(
            advertiser_id=advertiser_id,
            impressions_limit=campaign_data.impressions_limit,
            clicks_limit=campaign_data.clicks_limit,
            cost_per_impression=campaign_data.cost_per_impression,
            cost_per_click=campaign_data.cost_per_click,
            ad_title=campaign_data.ad_title,
            ad_text=campaign_data.ad_text,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            targeting=complete_targeting
        )
        self.session.add(new_campaign)
        await self.session.commit()
        await self.session.refresh(new_campaign)
        new_campaign.cost_per_impression = float(new_campaign.cost_per_impression)
        new_campaign.cost_per_click = float(new_campaign.cost_per_click)
        return new_campaign

    async def list_active_campaigns(self, current_day: int) -> list[Campaign]:
        stmt = select(Campaign).where(
            Campaign.start_date <= current_day,
            Campaign.end_date >= current_day
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_all_campaigns(self, advertiser_id: UUID, page: int, size: int) -> list[Campaign]:
        offset = (page - 1) * size
        stmt = select(Campaign).where(
            Campaign.advertiser_id == advertiser_id
        ).order_by(Campaign.start_date).offset(offset).limit(size)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_campaign(self, advertiser_id: UUID, campaign_id: UUID, update_data: CampaignUpdate) -> Campaign:
        campaign = await self.get_campaign_by_id(advertiser_id, campaign_id)
        if not campaign:
            return None

        original_start_date = campaign.start_date
        current_day_raw = await redis_client.get("current_day")
        current_day = (int(current_day_raw.decode() if isinstance(current_day_raw, bytes) else current_day_raw)
                       if current_day_raw else None)

        update_data = await validate_campaign_update(update_data.model_dump(), current_day)

        for field in update_data.model_fields:
            if field == "targeting":
                if update_data.targeting is None or field not in update_data.model_fields_set:
                    complete_targeting = {"gender": None, "age_from": None, "age_to": None, "location": None}
                else:
                    targeting_data = update_data.targeting.model_dump(exclude_unset=False)
                    complete_targeting = {
                        "gender": targeting_data.get("gender"),
                        "age_from": targeting_data.get("age_from"),
                        "age_to": targeting_data.get("age_to"),
                        "location": targeting_data.get("location")
                    }
                setattr(campaign, field, complete_targeting)

            elif field in {"start_date", "end_date"}:
                if field in update_data.model_fields_set:
                    new_value = getattr(update_data, field)
                else:
                    new_value = getattr(campaign, field)
                if (current_day is not None and campaign.start_date is not None and
                    int(current_day) >= int(original_start_date) and
                    int(new_value) != int(getattr(campaign, field))):
                    raise ValueError(f"{field} не может быть изменена после старта кампании")
                setattr(campaign, field, new_value)

            elif field in {"impressions_limit", "clicks_limit"}:
                if field in update_data.model_fields_set:
                    new_value = getattr(update_data, field)
                else:
                    new_value = getattr(campaign, field)
                if (current_day is not None and campaign.start_date is not None and
                    current_day >= int(original_start_date) and
                    int(new_value) != int(getattr(campaign, field))):
                    raise ValueError(f"{field} не может быть изменен после старта кампании")
                setattr(campaign, field, new_value)

            else:
                if field in update_data.model_fields_set:
                    value = getattr(update_data, field)
                    if field in {"cost_per_impression", "cost_per_click"} and not isinstance(value, Decimal):
                        value = Decimal(str(value))
                else:
                    value = getattr(campaign, field)
                setattr(campaign, field, value)

        try:
            await self.session.commit()
        except StaleDataError:
            await self.session.rollback()
            campaign = await self.get_campaign_by_id(advertiser_id, campaign_id)
        await self.session.refresh(campaign)
        campaign.cost_per_impression = float(campaign.cost_per_impression)
        campaign.cost_per_click = float(campaign.cost_per_click)
        return campaign

    async def get_campaign_by_id(self, advertiser_id: UUID, campaign_id: UUID) -> Campaign:
        stmt = select(Campaign).where(
            Campaign.campaign_id == campaign_id,
            Campaign.advertiser_id == advertiser_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_campaign_by_id_only(self, campaign_id: UUID) -> Campaign:
        stmt = select(Campaign).where(Campaign.campaign_id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_campaign(self, advertiser_id: UUID, campaign_id: UUID) -> bool:
        campaign = await self.get_campaign_by_id(advertiser_id, campaign_id)
        if not campaign:
            return False
        await self.session.delete(campaign)
        await self.session.commit()
        return True

    async def log_impression(self, campaign_id: UUID, client_id: UUID, redis_client_instance) -> int:
        global_key = f"campaign:{campaign_id}:impressions"
        already_seen = await redis_client_instance.sismember(global_key, str(client_id))
        if not already_seen:
            await redis_client_instance.sadd(global_key, str(client_id))

            current_day_raw = await redis_client_instance.get("current_day")
            current_day = (int(current_day_raw.decode() if isinstance(current_day_raw, bytes) else current_day_raw)
                           if current_day_raw else 0)
            daily_key = f"campaign:{campaign_id}:daily:impressions:{current_day}"
            await redis_client_instance.sadd(daily_key, str(client_id))

            campaign = await self.get_campaign_by_id_only(campaign_id)
            if campaign:
                spent_global_key = f"campaign:{campaign_id}:spent_impressions"
                spent_daily_key = f"campaign:{campaign_id}:daily:spent_impressions:{current_day}"
                await redis_client_instance.incrbyfloat(spent_global_key, float(campaign.cost_per_impression))
                await redis_client_instance.incrbyfloat(spent_daily_key, float(campaign.cost_per_impression))
                ad_impressions_total.labels(campaign_id=str(campaign_id)).inc()
                ad_impression_revenue.labels(campaign_id=str(campaign_id)).inc(float(campaign.cost_per_impression))
        return await redis_client_instance.scard(global_key)

    async def log_click(self, campaign_id: UUID, client_id: UUID, redis_client_instance) -> int:
        impressions_key = f"campaign:{campaign_id}:impressions"
        has_seen = await redis_client_instance.sismember(impressions_key, str(client_id))
        if not has_seen:
            return await redis_client_instance.scard(f"campaign:{campaign_id}:clicks")

        global_key = f"campaign:{campaign_id}:clicks"
        already_clicked = await redis_client_instance.sismember(global_key, str(client_id))
        if not already_clicked:
            await redis_client_instance.sadd(global_key, str(client_id))

            current_day_raw = await redis_client_instance.get("current_day")
            current_day = (int(current_day_raw.decode() if isinstance(current_day_raw, bytes) else current_day_raw)
                           if current_day_raw else 0)
            daily_key = f"campaign:{campaign_id}:daily:clicks:{current_day}"
            await redis_client_instance.sadd(daily_key, str(client_id))

            campaign = await self.get_campaign_by_id_only(campaign_id)
            if campaign:
                spent_global_key = f"campaign:{campaign_id}:spent_clicks"
                spent_daily_key = f"campaign:{campaign_id}:daily:spent_clicks:{current_day}"
                await redis_client_instance.incrbyfloat(spent_global_key, float(campaign.cost_per_click))
                await redis_client_instance.incrbyfloat(spent_daily_key, float(campaign.cost_per_click))
                ad_clicks_total.labels(campaign_id=str(campaign_id)).inc()
                ad_click_revenue.labels(campaign_id=str(campaign_id)).inc(float(campaign.cost_per_click))
        return await redis_client_instance.scard(global_key)

    async def log_ml_score(self, campaign_id: UUID, score: float) -> None:
        key = f"campaign:{campaign_id}:ml_scores"
        await redis_client.rpush(key, score)

    async def get_average_ml_score(self, campaign_id: UUID) -> float:
        key = f"campaign:{campaign_id}:ml_scores"
        scores = await redis_client.lrange(key, 0, -1)
        if not scores:
            return 0.0
        scores = [Decimal(s.decode() if isinstance(s, bytes) else s) for s in scores]
        avg = sum(scores) / Decimal(len(scores))
        return float(avg)

    async def get_impressions_count(self, campaign_id: UUID, redis_client_instance) -> int:
        key = f"campaign:{campaign_id}:impressions"
        return await redis_client_instance.scard(key)

    async def get_clicks_count(self, campaign_id: UUID, redis_client_instance) -> int:
        key = f"campaign:{campaign_id}:clicks"
        return await redis_client_instance.scard(key)

    async def get_campaign_stats(self, campaign_id: UUID, redis_client_instance) -> dict:
        campaign = await self.get_campaign_by_id_only(campaign_id)
        if not campaign:
            return None

        impressions = await redis_client_instance.scard(f"campaign:{campaign_id}:impressions")
        clicks = await redis_client_instance.scard(f"campaign:{campaign_id}:clicks")
        spent_imp_raw = await redis_client_instance.get(f"campaign:{campaign_id}:spent_impressions")
        spent_clicks_raw = await redis_client_instance.get(f"campaign:{campaign_id}:spent_clicks")
        spent_imp = (Decimal(spent_imp_raw.decode() if isinstance(spent_imp_raw, bytes) else spent_imp_raw)
                     if spent_imp_raw else Decimal("0.00"))
        spent_clicks = (Decimal(spent_clicks_raw.decode() if isinstance(spent_clicks_raw, bytes) else spent_clicks_raw)
                        if spent_clicks_raw else Decimal("0.00"))
        spent_total = spent_imp + spent_clicks
        conversion = (Decimal(clicks) / Decimal(impressions) * Decimal("100")) if impressions > 0 else Decimal("0.0")
        return {
            "impressions_count": impressions,
            "clicks_count": clicks,
            "conversion": float(conversion),
            "spent_impressions": float(spent_imp),
            "spent_clicks": float(spent_clicks),
            "spent_total": float(spent_total)
        }

    async def get_campaign_daily_stats(self, campaign_id: UUID, redis_client_instance) -> list[dict]:
        """
        Возвращает список статистики по дням от start_date кампании до последнего дня,
        который равен текущему дню (если кампания активна) или до end_date (если она закончилась).
        Если за день кликов > 0, а показов = 0, то все показатели за этот день возвращаются как 0.
        """
        campaign = await self.get_campaign_by_id_only(campaign_id)
        if not campaign:
            return []

        current_day_raw = await redis_client_instance.get("current_day")
        current_day = (int(current_day_raw.decode() if isinstance(current_day_raw, bytes) else current_day_raw)
                       if current_day_raw else 0)
        last_day = current_day if current_day <= campaign.end_date else campaign.end_date

        stats = []
        for day in range(campaign.start_date, last_day + 1):
            impressions_key = f"campaign:{campaign_id}:daily:impressions:{day}"
            clicks_key = f"campaign:{campaign_id}:daily:clicks:{day}"
            spent_imp_key = f"campaign:{campaign_id}:daily:spent_impressions:{day}"
            spent_clicks_key = f"campaign:{campaign_id}:daily:spent_clicks:{day}"

            imp = await redis_client_instance.scard(impressions_key)
            clicks = await redis_client_instance.scard(clicks_key)
            spent_imp_raw = await redis_client_instance.get(spent_imp_key)
            spent_clicks_raw = await redis_client_instance.get(spent_clicks_key)

            spent_imp = (Decimal(spent_imp_raw.decode() if isinstance(spent_imp_raw, bytes) else spent_imp_raw)
                         if spent_imp_raw else Decimal("0.00"))
            spent_clicks = (Decimal(spent_clicks_raw.decode() if isinstance(spent_clicks_raw, bytes) else spent_clicks_raw)
                            if spent_clicks_raw else Decimal("0.00"))

            if imp == 0 and clicks > 0:
                imp = 0
                clicks = 0
                spent_imp = Decimal("0.00")
                spent_clicks = Decimal("0.00")

            spent_total = spent_imp + spent_clicks
            conversion = (Decimal(clicks) / Decimal(imp) * Decimal("100")) if imp > 0 else Decimal("0.0")

            stats.append({
                "date": day,
                "impressions_count": imp,
                "clicks_count": clicks,
                "conversion": float(conversion),
                "spent_impressions": float(spent_imp),
                "spent_clicks": float(spent_clicks),
                "spent_total": float(spent_total)
            })
        stats.sort(key=lambda x: x["date"])
        return stats

    async def get_advertiser_stats(self, advertiser_id: UUID, redis_client_instance) -> dict:
        campaigns = await self.list_all_campaigns(advertiser_id, page=1, size=1000)
        if not campaigns:
            adv_repo = AdvertiserRepository(self.session)
            advertiser = await adv_repo.get_by_id(advertiser_id)
            if not advertiser:
                return None
            return {
                "impressions_count": 0,
                "clicks_count": 0,
                "spent_impressions": 0.0,
                "spent_clicks": 0.0,
                "spent_total": 0.0,
                "conversion": 0.0
            }
        aggregated = {
            "impressions_count": 0,
            "clicks_count": 0,
            "spent_impressions": Decimal("0.00"),
            "spent_clicks": Decimal("0.00"),
            "spent_total": Decimal("0.00")
        }
        for campaign in campaigns:
            stats = await self.get_campaign_stats(campaign.campaign_id, redis_client_instance)
            if stats is None:
                continue
            aggregated["impressions_count"] += stats.get("impressions_count", 0)
            aggregated["clicks_count"] += stats.get("clicks_count", 0)
            aggregated["spent_impressions"] += Decimal(str(stats.get("spent_impressions", 0.0)))
            aggregated["spent_clicks"] += Decimal(str(stats.get("spent_clicks", 0.0)))
            aggregated["spent_total"] += Decimal(str(stats.get("spent_total", 0.0)))
        if aggregated["impressions_count"] > 0:
            conversion = (Decimal(aggregated["clicks_count"]) / Decimal(aggregated["impressions_count"]) * Decimal("100"))
        else:
            conversion = Decimal("0.0")
        return {
            "impressions_count": aggregated["impressions_count"],
            "clicks_count": aggregated["clicks_count"],
            "spent_impressions": float(aggregated["spent_impressions"]),
            "spent_clicks": float(aggregated["spent_clicks"]),
            "spent_total": float(aggregated["spent_total"]),
            "conversion": float(conversion)
        }

    async def get_advertiser_daily_stats(self, advertiser_id: UUID, redis_client_instance) -> list[dict]:
        campaigns = await self.list_all_campaigns(advertiser_id, page=1, size=1000)
        if not campaigns:
            adv_repo = AdvertiserRepository(self.session)
            advertiser = await adv_repo.get_by_id(advertiser_id)
            if not advertiser:
                return None
            return []

        min_day = min(campaign.start_date for campaign in campaigns)
        current_day_raw = await redis_client_instance.get("current_day")
        current_day = (int(current_day_raw.decode() if isinstance(current_day_raw, bytes) else current_day_raw)
                       if current_day_raw else 0)
        daily_agg = {day: {"impressions_count": 0, "clicks_count": 0,
                           "spent_impressions": Decimal("0.00"), "spent_clicks": Decimal("0.00"),
                           "spent_total": Decimal("0.00")}
                     for day in range(min_day, current_day + 1)}
        for campaign in campaigns:
            daily_stats = await self.get_campaign_daily_stats(campaign.campaign_id, redis_client_instance)
            for stat in daily_stats:
                day = stat["date"]
                daily_agg[day]["impressions_count"] += stat.get("impressions_count", 0)
                daily_agg[day]["clicks_count"] += stat.get("clicks_count", 0)
                daily_agg[day]["spent_impressions"] += Decimal(str(stat.get("spent_impressions", 0.0)))
                daily_agg[day]["spent_clicks"] += Decimal(str(stat.get("spent_clicks", 0.0)))
                daily_agg[day]["spent_total"] += Decimal(str(stat.get("spent_total", 0.0)))
        result = []
        for day in range(min_day, current_day + 1):
            data = daily_agg[day]
            conversion = (Decimal(data["clicks_count"]) / Decimal(data["impressions_count"]) * Decimal("100")
                          if data["impressions_count"] > 0 else Decimal("0.0"))
            data["conversion"] = float(conversion)
            data["date"] = day
            data["spent_impressions"] = float(data["spent_impressions"])
            data["spent_clicks"] = float(data["spent_clicks"])
            data["spent_total"] = float(data["spent_total"])
            result.append(data)
        result.sort(key=lambda x: x["date"])
        return result
