import os
import json
from fastapi import HTTPException, status
from openai import AsyncOpenAI
from src.backend.cache import redis_client
from src.backend.metrics import api_errors_total

async def moderate_text(text: str) -> dict:
    """
    Использует модель gpt-4o-mini для проверки текста на наличие нежелательного контента.
    Отправляет запрос с инструкцией вернуть результат в формате JSON.
    Если переменная OPENAI_API_KEY не задана или возникает ошибка, возвращает безопасный ответ.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM API key not configured"
        )

    client = AsyncOpenAI(api_key=api_key)

    prompt = (
        "Проанализируй следующий текст и определи, содержит ли он нежелательный контент, "
        "который может включать, но не ограничиваться: нецензурной лексикой, угрозами, оскорблениями, ненавистническими высказываниями, "
        "упоминаниями наркотиков, а также рекламой или упоминанием сексшопов, интимными услугами,"
        "азартными играми и казино, табачных изделий, оружия, экстремистских материалов, "
        "порнографического содержания и других запрещённых тем по законодательству Российской Федерации.\n"
        "Если текст содержит такой контент, включая любые упоминания запрещённых тем, ответь в формате JSON: "
        "{'flagged': true, 'reason': 'описание причины'}.\n"
        "Если текст не содержит запрещённого контента, ответь: {'flagged': false}.\n\n"
        "Текст:\n" + text
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": ("Ты – ассистент модерации. "
                                "Твой ответ должен быть строго в формате JSON, без дополнительных комментариев.")
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            max_tokens=50
        )
    except Exception as e:
        api_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка модерации: {str(e)}"
        )

    content = response.choices[0].message.content.strip()
    try:
        result = json.loads(content.replace("'", "\""))
    except Exception as e:
        api_errors_total.inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка модерации: {str(e)}"
        )

    return {"results": [result]}


async def should_moderate() -> bool:
    """
    Возвращает True, если модерация включена (значение в Redis равно "1"),
    иначе False. При отсутствии ключа по умолчанию считается, что модерация отключена.
    """
    stored = await redis_client.get("moderation_enabled")
    if stored is None:
        return False
    if isinstance(stored, bytes):
        stored = stored.decode()
    return stored == "1"
