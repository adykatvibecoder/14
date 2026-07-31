from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.sql import func
from database.db import Session
from database.models import User
from services.brawl_api import get_player, is_tag_in_club
from config import VERIFY_CLUB_TAG
import hashlib

router = Router()

class Registration(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_tag = State()
    waiting_for_email = State()
    waiting_for_password = State()
    waiting_for_verify = State()

class Login(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль")],
            [KeyboardButton(text="Регистрация"), KeyboardButton(text="Вход")]
        ],
        resize_keyboard=True
    )

# Вход
@router.message(F.text == "Вход")
async def login_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Login.waiting_for_login)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Введите почту или никнейм:", reply_markup=kb)

@router.message(Login.waiting_for_login, F.text == "Отмена")
async def login_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_main_keyboard())

@router.message(Login.waiting_for_login)
async def login_check(message: Message, state: FSMContext):
    login = message.text.strip()
    session = Session()
    user = session.query(User).filter(
        (User.email == login) | (User.nickname == login)
    ).first()
    
    if not user:
        await message.answer("Аккаунт не найден. Попробуйте снова или нажмите Отмена.")
        session.close()
        return
    
    await state.update_data(user_id=user.id)
    session.close()
    await state.set_state(Login.waiting_for_password)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Введите пароль:", reply_markup=kb)

@router.message(Login.waiting_for_password, F.text == "Отмена")
async def login_password_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_main_keyboard())

@router.message(Login.waiting_for_password)
async def login_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    
    session = Session()
    user = session.query(User).filter_by(id=data["user_id"]).first()
    
    if not user or user.password_hash != hash_password(password):
        await message.answer("Неверный пароль. Попробуйте снова или нажмите Отмена.")
        session.close()
        return
    
    user.telegram_id = message.from_user.id
    user.last_login = func.now()
    session.commit()
    session.close()
    
    await state.clear()
    await message.answer(
        f"Добро пожаловать, {user.nickname}!",
        reply_markup=get_main_keyboard()
    )

# Старт
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    await message.answer(
        "Добро пожаловать в ESBrawlElite!\n"
        "Первый FaceIt ладдер в Brawl Stars.\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )

# Регистрация
@router.message(F.text == "Регистрация")
async def register_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Registration.waiting_for_nickname)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Придумайте никнейм:", reply_markup=kb)

@router.message(Registration.waiting_for_nickname, F.text == "Отмена")
async def reg_cancel_nickname(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_main_keyboard())

@router.message(Registration.waiting_for_nickname)
async def register_nickname(message: Message, state: FSMContext):
    nickname = message.text.strip()
    if len(nickname) < 3 or len(nickname) > 20:
        await message.answer("Никнейм должен быть от 3 до 20 символов.")
        return
    await state.update_data(nickname=nickname)
    await state.set_state(Registration.waiting_for_tag)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Введите ваш тег Brawl Stars (например #ABC123):", reply_markup=kb)

@router.message(Registration.waiting_for_tag, F.text == "Отмена")
async def reg_cancel_tag(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_main_keyboard())

@router.message(Registration.waiting_for_tag)
async def register_tag(message: Message, state: FSMContext):
    tag = message.text.strip().replace("#", "")
    tag = f"#{tag}"
    
    player = get_player(tag)
    if not player:
        await message.answer("Тег не найден. Проверьте и попробуйте снова или нажмите Отмена.")
        return
    
    brawl_name = player["name"]
    await state.update_data(brawl_tag=tag, brawl_name=brawl_name)
    await state.set_state(Registration.waiting_for_email)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer(f"Аккаунт найден: {brawl_name}\n\nВведите вашу почту:", reply_markup=kb)

@router.message(Registration.waiting_for_email, F.text == "Отмена")
async def reg_cancel_email(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_main_keyboard())

@router.message(Registration.waiting_for_email)
async def register_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email:
        await message.answer("Некорректная почта. Попробуйте снова или нажмите Отмена.")
        return
    await state.update_data(email=email)
    await state.set_state(Registration.waiting_for_password)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer("Придумайте пароль:", reply_markup=kb)

@router.message(Registration.waiting_for_password, F.text == "Отмена")
async def reg_cancel_password(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_main_keyboard())

@router.message(Registration.waiting_for_password)
async def register_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 6:
        await message.answer("Пароль должен быть не менее 6 символов. Попробуйте снова или нажмите Отмена.")
        return
    
    data = await state.get_data()
    
    session = Session()
    existing = session.query(User).filter(
        (User.email == data["email"]) | 
        (User.nickname == data["nickname"]) |
        (User.brawl_tag == data["brawl_tag"])
    ).first()
    
    if existing:
        if existing.nickname == data["nickname"]:
            await message.answer("Этот никнейм уже занят. Нажмите Отмена и попробуйте другой.")
        elif existing.email == data["email"]:
            await message.answer("Эта почта уже используется. Нажмите Отмена и попробуйте другую.")
        elif existing.brawl_tag == data["brawl_tag"]:
            await message.answer("Этот тег уже зарегистрирован. Нажмите Отмена.")
        else:
            await message.answer("Аккаунт с такими данными уже существует. Нажмите Отмена.")
        session.close()
        return
    
    user = User(
        telegram_id=message.from_user.id,
        nickname=data["nickname"],
        brawl_tag=data["brawl_tag"],
        brawl_name=data["brawl_name"],
        email=data["email"],
        password_hash=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.close()
    
    await state.set_state(Registration.waiting_for_verify)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Я вступил в клан"), KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    await message.answer(
        f"Для подтверждения аккаунта вступите в клан:\n"
        f"Тег: {VERIFY_CLUB_TAG}\n"
        f"Требования: 30 000 кубков\n\n"
        f"Как вступили — нажмите кнопку:",
        reply_markup=kb
    )

@router.message(Registration.waiting_for_verify, F.text == "Отмена")
async def reg_cancel_verify(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Регистрация отменена.", reply_markup=get_main_keyboard())

@router.message(Registration.waiting_for_verify, F.text == "Я вступил в клан")
async def register_verify(message: Message, state: FSMContext):
    data = await state.get_data()
    tag = data["brawl_tag"]
    
    if is_tag_in_club(tag, VERIFY_CLUB_TAG):
        session = Session()
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            user.verified = True
            session.commit()
        session.close()
        
        await state.clear()
        await message.answer(
            "Аккаунт подтвержден! Теперь вы можете выйти из клана.\n"
            "Добро пожаловать в ESBrawlElite!",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer("Вы не найдены в клане. Вступите и попробуйте снова или нажмите Отмена.")
