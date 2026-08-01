import json
import hashlib
import os
import uuid
import random
import string
import base64
from aiohttp import web
from sqlalchemy import func
from database.db import Session
from database.models import User, FriendRequest, Room, RoomMember, Message
from services.brawl_api import is_tag_in_club
from config import VERIFY_CLUB_TAG

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
AVATAR_DIR = os.path.join(DATA_DIR, "avatars")
BANNER_DIR = os.path.join(DATA_DIR, "banners")
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(BANNER_DIR, exist_ok=True)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def user_profile(u):
    return {
        "id": u.id,
        "nickname": u.nickname,
        "brawl_tag": u.brawl_tag,
        "brawl_name": u.brawl_name,
        "elo": u.elo,
        "wins": u.wins,
        "losses": u.losses,
        "games": u.wins + u.losses,
        "winrate": round(u.wins / (u.wins + u.losses) * 100, 1) if (u.wins + u.losses) > 0 else 0,
        "reg_date": u.created_at.strftime("%d.%m.%Y") if u.created_at else "—",
        "description": u.description or "",
        "verified": u.verified,
        "avatarUrl": u.avatar_url or "",
        "bannerUrl": u.banner_url or "",
        "language": u.language or "ru",
        "theme": u.theme or "light",
        "sound": u.sound,
        "notifications": u.notifications,
        "color_theme": u.color_theme or "#e94560"
    }

# ------------------- auth -------------------
async def login(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    login_raw = data.get("login", "")
    password = data.get("password", "")
    if not login_raw or not password:
        return web.json_response({"error": "login and password required"}, status=400)
    login_lower = login_raw.strip().lower()
    session = Session()
    user = session.query(User).filter(
        (func.lower(User.email) == login_lower) |
        (func.lower(User.nickname) == login_lower) |
        (User.brawl_tag == login_raw.strip().upper())
    ).first()
    if not user or user.password_hash != hash_password(password):
        session.close()
        return web.json_response({"error": "Invalid credentials"}, status=401)
    profile = user_profile(user)
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
    profile = user_profile(user)
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

async def change_password(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    user_id = data.get("user_id")
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not all([user_id, old_password, new_password]):
        return web.json_response({"error": "All fields required"}, status=400)
    session = Session()
    user = session.query(User).filter_by(id=int(user_id)).first()
    if not user or user.password_hash != hash_password(old_password):
        session.close()
        return web.json_response({"error": "Invalid old password"}, status=401)
    if len(new_password) < 6:
        session.close()
        return web.json_response({"error": "Password too short"}, status=400)
    user.password_hash = hash_password(new_password)
    session.commit()
    session.close()
    return web.json_response({"success": True})

async def update_profile(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    user_id = data.get("user_id")
    if not user_id:
        return web.json_response({"error": "user_id required"}, status=400)
    session = Session()
    user = session.query(User).filter_by(id=int(user_id)).first()
    if not user:
        session.close()
        return web.json_response({"error": "User not found"}, status=404)
    updatable = ["description", "language", "theme", "sound", "notifications", "color_theme", "avatar_url", "banner_url"]
    for field in updatable:
        if field in data:
            setattr(user, field, data[field])
    session.commit()
    session.close()
    return web.json_response({"success": True})

# ------------------- leaderboard -------------------
async def get_leaderboard(request):
    limit = int(request.rel_url.query.get("limit", 50))
    session = Session()
    users = session.query(User).filter(User.verified == True).order_by(User.elo.desc()).limit(limit).all()
    result = []
    for i, u in enumerate(users, 1):
        result.append({
            "rank": i,
            "id": u.id,
            "nickname": u.nickname,
            "brawl_tag": u.brawl_tag,
            "elo": u.elo,
            "avatarUrl": u.avatar_url or ""
        })
    session.close()
    return web.json_response(result)

# ------------------- friends -------------------
async def get_friends(request):
    user_id = int(request.rel_url.query.get("user_id"))
    session = Session()
    sent = session.query(FriendRequest).filter(FriendRequest.from_user_id == user_id, FriendRequest.status == "accepted").all()
    received = session.query(FriendRequest).filter(FriendRequest.to_user_id == user_id, FriendRequest.status == "accepted").all()
    friends = []
    for f in sent:
        friends.append(user_profile(f.to_user))
    for f in received:
        friends.append(user_profile(f.from_user))
    session.close()
    return web.json_response(friends)

async def get_friend_requests(request):
    user_id = int(request.rel_url.query.get("user_id"))
    session = Session()
    pending = session.query(FriendRequest).filter(FriendRequest.to_user_id == user_id, FriendRequest.status == "pending").all()
    result = []
    for fr in pending:
        result.append({
            "request_id": fr.id,
            "from_user": user_profile(fr.from_user)
        })
    session.close()
    return web.json_response(result)

async def send_friend_request(request):
    data = await request.json()
    from_id = data.get("from_user_id")
    to_id = data.get("to_user_id")
    if not from_id or not to_id:
        return web.json_response({"error": "from_user_id and to_user_id required"}, status=400)
    session = Session()
    existing = session.query(FriendRequest).filter(
        ((FriendRequest.from_user_id == from_id) & (FriendRequest.to_user_id == to_id)) |
        ((FriendRequest.from_user_id == to_id) & (FriendRequest.to_user_id == from_id))
    ).first()
    if existing:
        session.close()
        return web.json_response({"error": "Request already exists"}, status=409)
    fr = FriendRequest(from_user_id=from_id, to_user_id=to_id, status="pending")
    session.add(fr)
    session.commit()
    session.close()
    return web.json_response({"success": True})

async def accept_friend_request(request):
    data = await request.json()
    request_id = data.get("request_id")
    session = Session()
    fr = session.query(FriendRequest).filter_by(id=request_id).first()
    if not fr or fr.status != "pending":
        session.close()
        return web.json_response({"error": "Invalid request"}, status=404)
    fr.status = "accepted"
    session.commit()
    session.close()
    return web.json_response({"success": True})

async def reject_friend_request(request):
    data = await request.json()
    request_id = data.get("request_id")
    session = Session()
    fr = session.query(FriendRequest).filter_by(id=request_id).first()
    if fr:
        session.delete(fr)
        session.commit()
    session.close()
    return web.json_response({"success": True})

async def remove_friend(request):
    data = await request.json()
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")
    session = Session()
    fr = session.query(FriendRequest).filter(
        ((FriendRequest.from_user_id == user_id) & (FriendRequest.to_user_id == friend_id)) |
        ((FriendRequest.from_user_id == friend_id) & (FriendRequest.to_user_id == user_id)),
        FriendRequest.status == "accepted"
    ).first()
    if fr:
        session.delete(fr)
        session.commit()
    session.close()
    return web.json_response({"success": True})

# ------------------- rooms -------------------
def generate_room_code(session):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not session.query(Room).filter_by(code=code).first():
            return code

async def create_room(request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        return web.json_response({"error": "user_id required"}, status=400)
    session = Session()
    code = generate_room_code(session)
    room = Room(id=str(uuid.uuid4()), code=code, host_id=user_id)
    session.add(room)
    session.flush()
    member = RoomMember(room_id=room.id, user_id=user_id)
    session.add(member)
    session.commit()
    session.close()
    return web.json_response({"room_id": room.id, "code": code})

async def join_room(request):
    data = await request.json()
    user_id = data.get("user_id")
    code = data.get("code")
    if not user_id or not code:
        return web.json_response({"error": "user_id and code required"}, status=400)
    session = Session()
    room = session.query(Room).filter_by(code=code.upper()).first()
    if not room:
        session.close()
        return web.json_response({"error": "Room not found"}, status=404)
    if len(room.members) >= 3:
        session.close()
        return web.json_response({"error": "Room is full"}, status=400)
    if any(m.user_id == user_id for m in room.members):
        session.close()
        return web.json_response({"error": "Already in room"}, status=400)
    member = RoomMember(room_id=room.id, user_id=user_id)
    session.add(member)
    session.commit()
    session.close()
    return web.json_response({"success": True})

async def leave_room(request):
    data = await request.json()
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    if not user_id or not room_id:
        return web.json_response({"error": "user_id and room_id required"}, status=400)
    session = Session()
    member = session.query(RoomMember).filter_by(room_id=room_id, user_id=user_id).first()
    if member:
        session.delete(member)
        session.commit()
    session.close()
    return web.json_response({"success": True})

async def disband_room(request):
    data = await request.json()
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    if not user_id or not room_id:
        return web.json_response({"error": "user_id and room_id required"}, status=400)
    session = Session()
    room = session.query(Room).filter_by(id=room_id).first()
    if not room or room.host_id != user_id:
        session.close()
        return web.json_response({"error": "Only host can disband"}, status=403)
    session.delete(room)
    session.commit()
    session.close()
    return web.json_response({"success": True})

async def get_room(request):
    room_id = request.match_info.get("room_id")
    session = Session()
    room = session.query(Room).filter_by(id=room_id).first()
    if not room:
        session.close()
        return web.json_response({"error": "Room not found"}, status=404)
    members = []
    for m in room.members:
        u = session.query(User).filter_by(id=m.user_id).first()
        members.append({
            "user_id": u.id,
            "nickname": u.nickname,
            "brawl_tag": u.brawl_tag,
            "avatar_color": u.avatar_url or f"hsl({hash(u.nickname) % 360}, 70%, 60%)",
            "is_host": u.id == room.host_id
        })
    result = {
        "id": room.id,
        "code": room.code,
        "host_id": room.host_id,
        "members": members
    }
    session.close()
    return web.json_response(result)

# ------------------- chat -------------------
async def send_message(request):
    data = await request.json()
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    text = data.get("text")
    if not all([room_id, user_id, text]):
        return web.json_response({"error": "room_id, user_id, text required"}, status=400)
    session = Session()
    member = session.query(RoomMember).filter_by(room_id=room_id, user_id=user_id).first()
    if not member:
        session.close()
        return web.json_response({"error": "Not a member"}, status=403)
    msg = Message(room_id=room_id, sender_id=user_id, text=text)
    session.add(msg)
    session.commit()
    session.close()
    return web.json_response({"success": True})

async def get_messages(request):
    room_id = request.rel_url.query.get("room_id")
    since = int(request.rel_url.query.get("since", "0"))
    session = Session()
    msgs = session.query(Message).filter(Message.room_id == room_id, Message.id > since).order_by(Message.id.asc()).all()
    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "sender": m.sender.nickname,
            "text": m.text,
            "time": m.created_at.strftime("%H:%M") if m.created_at else ""
        })
    session.close()
    return web.json_response(result)

# ------------------- avatar / banner -------------------
async def upload_avatar(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    user_id = data.get("user_id")
    image_b64 = data.get("image")
    if not user_id or not image_b64:
        return web.json_response({"error": "user_id and image required"}, status=400)
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]
    try:
        img_bytes = base64.b64decode(image_b64)
    except:
        return web.json_response({"error": "Invalid base64"}, status=400)
    filename = f"avatar_{user_id}.jpg"
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    url = f"/static/avatars/{filename}"
    session = Session()
    user = session.query(User).filter_by(id=int(user_id)).first()
    if user:
        user.avatar_url = url
        session.commit()
    session.close()
    return web.json_response({"success": True, "avatarUrl": url})

async def upload_banner(request):
    try:
        data = await request.json()
    except:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    user_id = data.get("user_id")
    image_b64 = data.get("image")
    if not user_id or not image_b64:
        return web.json_response({"error": "user_id and image required"}, status=400)
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]
    try:
        img_bytes = base64.b64decode(image_b64)
    except:
        return web.json_response({"error": "Invalid base64"}, status=400)
    filename = f"banner_{user_id}.jpg"
    filepath = os.path.join(BANNER_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    url = f"/static/banners/{filename}"
    session = Session()
    user = session.query(User).filter_by(id=int(user_id)).first()
    if user:
        user.banner_url = url
        session.commit()
    session.close()
    return web.json_response({"success": True, "bannerUrl": url})

async def get_banners(request):
    return web.json_response([])

async def select_banner(request):
    data = await request.json()
    user_id = data.get("user_id")
    banner_id = data.get("banner_id")
    session = Session()
    user = session.query(User).filter_by(id=int(user_id)).first()
    if user:
        # Здесь можно сохранить banner_id в отдельное поле, если оно есть
        session.commit()
    session.close()
    return web.json_response({"success": True})

# ------------------- battles (placeholder) -------------------
async def get_battles(request):
    return web.json_response([])
