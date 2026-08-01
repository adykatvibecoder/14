from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=True)   # теперь может быть NULL
    nickname = Column(String(50), unique=True, nullable=False)
    brawl_tag = Column(String(20), unique=True, nullable=False)
    brawl_name = Column(String(50))
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    elo = Column(Integer, default=1000)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    description = Column(String(200), default="")
    verified = Column(Boolean, default=False)
    language = Column(String(5), default="ru")
    theme = Column(String(10), default="dark")
    sound = Column(Boolean, default=True)
    notifications = Column(Boolean, default=True)
    color_theme = Column(String(20), default="blue")
    avatar_url = Column(String(500), default="")
    banner_url = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, server_default=func.now())
