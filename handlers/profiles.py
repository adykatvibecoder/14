from aiogram import Router, F
from aiogram.types import Message
from database.db import Session
from database.models import User

router = Router()

def get_division(elo: int) -> str:
    if elo < 1500:
        return "Бронза"
    elif elo < 2000:
        return "Серебро"
    elif elo < 2500:
        return "Золото"
    elif elo < 3000:
        return "Алмаз"
    elif elo < 3500:
        return "Мифик"
    elif elo < 4500:
        return "Легенда"
    elif elo < 6000:
        return "Мастер"
    else:
        return "PRO"

@router.message(F.text == "Профиль")
async def cmd_profile(message: Message):
    session = Session()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        session.close()
        return
    
    division = get_division(user.elo)
    total_games = user.wins + user.losses
    winrate = round(user.wins / total_games * 100, 1) if total_games > 0 else 0
    
    text = (
        f"Nickname: {user.nickname}\n"
        f"Tag: {user.brawl_tag} | {user.brawl_name}\n"
        f"Rank: {division} | {user.elo} ELO\n"
        f"Winrate: {winrate}%\n"
        f"Games: {total_games}\n"
        f"Wins: {user.wins}\n"
        f"Losses: {user.losses}\n\n"
        f"{user.description}"
    )
    
    await message.answer(text)
    session.close()
