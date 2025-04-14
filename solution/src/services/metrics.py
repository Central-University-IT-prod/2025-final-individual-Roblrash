import asyncio
import random
from src.backend.metrics import (
    ad_clicks_total,
    ad_impressions_total,
    ad_impression_revenue,
    ad_click_revenue,
    api_errors_total
)

CAMPAIGN_IDS = ["campaign1", "campaign2", "campaign3"]


async def simulate_day_and_metrics():
    """
    Фоновая задача: каждую секунду обновляет статистику (накручивает метрики) для заданных кампаний.
    """
    while True:
        for cid in CAMPAIGN_IDS:
            impressions = random.randint(10, 50)
            clicks = random.randint(0, impressions)
            revenue_impr = impressions * random.uniform(0.05, 0.2)
            revenue_click = clicks * random.uniform(0.5, 1.5)

            ad_impressions_total.labels(campaign_id=cid).inc(impressions)
            ad_clicks_total.labels(campaign_id=cid).inc(clicks)
            ad_impression_revenue.labels(campaign_id=cid).set(revenue_impr)
            ad_click_revenue.labels(campaign_id=cid).set(revenue_click)

        await asyncio.sleep(1)
