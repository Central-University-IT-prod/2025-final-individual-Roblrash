import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, campaigns, stats, images, moderation, ai_text

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(start.router)
dp.include_router(campaigns.router)
dp.include_router(stats.router)
dp.include_router(images.router)
dp.include_router(moderation.router)
dp.include_router(ai_text.router)

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.aclose()

if __name__ == "__main__":
    asyncio.run(main())
