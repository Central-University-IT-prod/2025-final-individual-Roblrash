from prometheus_client import Counter, Gauge

ad_clicks_total = Counter(
    'ad_clicks_total',
    'Общее количество кликов по рекламе',
    ['campaign_id']
)

ad_impressions_total = Counter(
    'ad_impressions_total',
    'Общее количество показов рекламы',
    ['campaign_id']
)

ad_impression_revenue = Gauge(
    'ad_impression_revenue',
    'Доход от показов рекламы',
    ['campaign_id']
)

ad_click_revenue = Gauge(
    'ad_click_revenue',
    'Доход от кликов рекламы',
    ['campaign_id']
)

api_errors_total = Counter(
    'api_errors_total',
    'Общее количество ошибок API'
)
