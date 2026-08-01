import json
import hashlib
from aiohttp import web
from database.db import Session
from database.models import User
from services.brawl_api import is_tag_in_club
from config import VERIFY_CLUB_TAG

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def login(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    login = data.get("login")
    password = data.get("password")
    if not login or not password:
        return web.json_response({"error": "login and password required"}, status=400)
    session = Session()
    user = session.query(User).filter(
        (User.email == login) | (User.nickname == login) | (User.brawl_tag == login)
    ).first()
    if not user or user.password_hash != hash_password(password):
        session.close()
        return web.json_response({"error": "Invalid credentials"}, status=401)
    session.commit()
    profile = {
        "id": user.id,
        "nickname": user.nickname,
        "brawl_tag": user.brawl_tag,
        "brawl_name": user.brawl_name,
        "elo": user.elo,
        "wins": user.wins,
        "losses": user.losses,
        "games": user.wins + user.losses,
        "winrate": round(user.wins / (user.wins + user.losses) * 100, 1) if (user.wins + user.losses) > 0 else 0,
        "reg_date": user.created_at.strftime("%d.%m.%Y") if user.created_at else "—",
        "description": user.description or "",
        "verified": user.verified,
        "avatarUrl": user.avatar_url or "",
        "bannerUrl": user.banner_url or ""
    }
    session.close()
    return web.json_response(profile)

async def register(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    nickname = data.get("nickname")
    tag = data.get("tag")
    email = data.get("email")
    password = data.get("password")
    if not all([nickname, tag, email, password]):
        return web.json_response({"error": "All fields required"}, status=400)
    if len(nickname) < 3:
        return web.json_response({"error": "Nickname too short"}, status=400)
    if not tag.startswith("#"):
        return web.json_response({"error": "Tag must start with #"}, status=400)
    if "@" not in email or "." not in email:
        return web.json_response({"error": "Invalid email"}, status=400)
    if len(password) < 6:
        return web.json_response({"error": "Password too short"}, status=400)
    session = Session()
    if session.query(User).filter((User.email == email) | (User.nickname == nickname) | (User.brawl_tag == tag)).first():
        session.close()
        return web.json_response({"error": "User already exists"}, status=409)
    user = User(
        telegram_id=0,
        nickname=nickname,
        brawl_tag=tag,
        email=email,
        password_hash=hash_password(password),
        brawl_name=data.get("brawl_name", ""),
        verified=False
    )
    session.add(user)
    session.commit()
    session.close()
    return web.json_response({"success": True, "message": "Registration successful. Verify club to activate."})

async def get_profile(request):
    user_id = request.rel_url.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "user_id required"}, status=400)
    session = Session()
    user = session.query(User).filter_by(id=int(user_id)).first()
    if not user:
        session.close()
        return web.json_response({"error": "User not found"}, status=404)
    profile = {
        "id": user.id,
        "nickname": user.nickname,
        "brawl_tag": user.brawl_tag,
        "brawl_name": user.brawl_name,
        "elo": user.elo,
        "wins": user.wins,
        "losses": user.losses,
        "games": user.wins + user.losses,
        "winrate": round(user.wins / (user.wins + user.losses) * 100, 1) if (user.wins + user.losses) > 0 else 0,
        "reg_date": user.created_at.strftime("%d.%m.%Y") if user.created_at else "—",
        "description": user.description or "",
        "verified": user.verified,
        "avatarUrl": user.avatar_url or "",
        "bannerUrl": user.banner_url or ""
    }
    session.close()
    return web.json_response(profile)

async def verify_club(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    tag = data.get("tag")
    user_id = data.get("user_id")
    if not tag or not user_id:
        return web.json_response({"error": "tag and user_id required"}, status=400)
    if is_tag_in_club(tag, VERIFY_CLUB_TAG):
        session = Session()
        user = session.query(User).filter_by(id=int(user_id)).first()
        if user:
            user.verified = True
            session.commit()
        session.close()
        return web.json_response({"success": True, "verified": True})
    else:
        return web.json_response({"success": False, "verified": False, "message": "Tag not found in club"})
