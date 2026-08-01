import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, WEBAPP_URL
from database.db import init_db
from handlers.auth import router as auth_router
from handlers.profile import router as profile_router
from api.auth import login, register, get_profile, verify_club, change_password
import os

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_router(auth_router)
dp.include_router(profile_router)

app = web.Application()

# Middleware для CORS
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        response = web.Response(status=204)
    else:
        response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

app.middlewares.append(cors_middleware)

# API маршруты
app.router.add_route('POST', '/api/login', login)
app.router.add_route('POST', '/api/register', register)
app.router.add_route('GET', '/api/profile', get_profile)
app.router.add_route('POST', '/api/verify-club', verify_club)
app.router.add_route('POST', '/api/change-password', change_password)

# Раздача Mini App (webapp/index.html)
async def webapp_handler(request):
    try:
        with open('webapp/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        return web.Response(text=html, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="App not found", status=404)

app.router.add_route('GET', '/app', webapp_handler)

# Главная страница API
async def index(request):
    return web.json_response({"status": "ok", "service": "ESBrawlElite API"})
app.router.add_route('GET', '/', index)

# Команда /start
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Открыть ESBrawlElite", web_app=WebAppInfo(url=f"{WEBAPP_URL}/app"))],
            [KeyboardButton(text="Профиль")],
            [KeyboardButton(text="Регистрация"), KeyboardButton(text="Вход")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать в ESBrawlElite!\n"
        "Первый FaceIt ладдер в Brawl Stars.\n\n"
        "Используйте кнопку ниже, чтобы открыть приложение:",
        reply_markup=kb
    )

async def main():
    init_db()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 3000)
    await site.start()
    print("ESBrawlElite API доступен на http://0.0.0.0:3000")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
