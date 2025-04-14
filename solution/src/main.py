from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
from src.backend import metrics
from src.routes import user, advertiser, ml_score, campaign, time, ads, stats, moderation, ad_AI_text, metrics_router
from src.backend.cache import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.set("current_day", 0)
    await redis_client.set("moderation_enabled", "0")
    yield

app = FastAPI(
    title="Ad Engine API",
    description="API для управления рекламными кампаниями",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Ошибка валидации"}
    )

app.include_router(user.router)
app.include_router(advertiser.router)
app.include_router(ml_score.router)
app.include_router(campaign.router)
app.include_router(ads.router)
app.include_router(stats.router)
app.include_router(time.router)
app.include_router(moderation.router)
app.include_router(ad_AI_text.router)
app.include_router(metrics_router.router)