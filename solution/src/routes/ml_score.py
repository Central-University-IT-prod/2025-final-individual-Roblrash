from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.ml_score import MLScore as MLScoreSchema
from src.repositories.ml_score import MLScoreRepository
from src.repositories.user import UserRepository
from src.repositories.advertiser import AdvertiserRepository
from src.backend.database import get_session

router = APIRouter(prefix="/ml-scores", tags=["ML Scores"])


@router.post("", response_model=MLScoreSchema)
async def upsert_ml_score(ml_data: MLScoreSchema, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    client = await user_repo.get_by_id(ml_data.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )

    advertiser_repo = AdvertiserRepository(session)
    advertiser = await advertiser_repo.get_by_id(ml_data.advertiser_id)
    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рекламодатель не найден"
        )

    ml_repo = MLScoreRepository(session)
    updated_ml = await ml_repo.upsert(ml_data)
    return updated_ml
