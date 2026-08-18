# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""SQLAlchemy ORM models for User, APIToken, UsageLog, Notification, and ChatMessage."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from api_service.auth.database import Base


def _generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # "superadmin" | "user"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    # Relationships
    api_token = relationship("APIToken", back_populates="user", uselist=False, cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class APIToken(Base):
    """API access token for programmatic REST access."""

    __tablename__ = "api_tokens"

    id = Column(String, primary_key=True, default=_generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    token_key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True, default="default")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_token")


class UsageLog(Base):
    """Tracks per-request usage (queries, chat, indexing)."""

    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    search_type = Column(String(50), nullable=True)  # local, global, drift, basic, chat
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True, default=0)
    latency_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=_utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")


class Notification(Base):
    """In-app notifications (e.g., indexing completion alerts)."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default="info")  # info, success, error
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")


class ChatMessage(Base):
    """Stores conversation history for the AI Chat interface."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    search_type_used = Column(String(50), nullable=True)  # Which search method was used
    tokens_used = Column(Integer, nullable=True, default=0)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_messages")
