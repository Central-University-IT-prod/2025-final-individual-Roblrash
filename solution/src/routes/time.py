from fastapi import APIRouter, HTTPException, status
from src.backend.cache import redis_client
from src.schemas.time import AdvanceTimeRequest, AdvanceTimeResponse

router = APIRouter(prefix="/time", tags=["Time"])


@router.post("/advance", response_model=AdvanceTimeResponse, status_code=status.HTTP_200_OK)
async def advance_time(request: AdvanceTimeRequest):
    stored_day = await redis_client.get("current_day")
    current_day = int(stored_day) if stored_day is not None else 0

    if request.current_date < current_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя установить день меньше текущего ({current_day})"
        )

    await redis_client.set("current_day", request.current_date)
    return AdvanceTimeResponse(current_date=request.current_date)
