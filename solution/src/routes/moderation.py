from fastapi import APIRouter, HTTPException, status
from src.backend.cache import redis_client
from src.schemas.moderation import ModerationToggleRequest, ModerationToggleResponse
from src.backend.metrics import api_errors_total

router = APIRouter(prefix="/moderation", tags=["Moderation"])

@router.post("/toggle", response_model=ModerationToggleResponse, status_code=status.HTTP_200_OK)
async def toggle_moderation(request: ModerationToggleRequest):
    """
    Переключатель режима модерации (включено, выключено).
    true - Включить,
    false - Выключить.
    """
    value = "1" if request.enabled else "0"
    try:
        await redis_client.set("moderation_enabled", value)
    except Exception as e:
        api_errors_total.inc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return ModerationToggleResponse(moderation_enabled=request.enabled)