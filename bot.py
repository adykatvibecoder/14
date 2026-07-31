import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database.db import init_db
from handlers.auth import router as auth_router
from handlers.profile import router as profile_router

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_router(auth_router)
dp.include_router(profile_router)

async def main():
    init_db()
    print("ESBrawlElite запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
