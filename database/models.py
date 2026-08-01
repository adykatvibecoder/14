from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=True)
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

    # связи
    sent_requests = relationship("FriendRequest", foreign_keys="[FriendRequest.from_user_id]", back_populates="from_user")
    received_requests = relationship("FriendRequest", foreign_keys="[FriendRequest.to_user_id]", back_populates="to_user")
    room_memberships = relationship("RoomMember", back_populates="user")
    sent_messages = relationship("Message", back_populates="sender")


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(10), default="pending")  # pending / accepted / rejected
    created_at = Column(DateTime, server_default=func.now())

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_requests")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_requests")


class Room(Base):
    __tablename__ = "rooms"
    id = Column(String(36), primary_key=True)  # uuid или code
    code = Column(String(6), unique=True, nullable=False)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    # участники и сообщения
    members = relationship("RoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")


class RoomMember(Base):
    __tablename__ = "room_members"
    id = Column(Integer, primary_key=True)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, server_default=func.now())
    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="room_memberships")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    room = relationship("Room", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
