from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import os
from openai import AsyncOpenAI
from src.schemas.ad_AI_text import AdTextRequest, AdTextResponse
from src.backend.database import get_session
from src.backend.metrics import api_errors_total
from src.services.moderation import moderate_text, should_moderate

router = APIRouter(tags=["AI_text"])

@router.post("/generate_ad_text", response_model=AdTextResponse)
async def generate_ad_text(
    request: AdTextRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Генерирует рекламный текст для объявления, используя LLM.
    На вход подаются название объявления и название рекламодателя.
    Если модерация включена, сгенерированный текст и заголовок проходят проверку.
    """
    if await should_moderate():
        mod_response_text = await moderate_text(request.advertiser_name)
        mod_response_title = await moderate_text(request.ad_title)
        if mod_response_text["results"][0].get("flagged"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сгенерированный рекламный текст не прошел модерацию"
            )
        if mod_response_title["results"][0].get("flagged"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заголовок объявления не прошел модерацию"
            )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM API key not configured"
        )

    client = AsyncOpenAI(api_key=api_key)

    prompt = (
        f"Сгенерируй лаконичный и креативный рекламный текст для объявления.\n"
        f"Название: {request.ad_title}\n"
        f"Рекламодатель: {request.advertiser_name}\n\n"
        "Текст должен быть емким, подчеркивать инновационность и высокое качество продукта, "
        "мотивировать к действию и не превышать 150 токенов."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты – опытный рекламный копирайтер, специализирующийся на создании привлекательных текстов."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=150
        )
    except Exception as e:
        api_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации текста: {str(e)}"
        )

    generated_text = response.choices[0].message.content.strip()
    cleaned_text = generated_text.strip(' "\'')

    return AdTextResponse(ad_text=cleaned_text)
