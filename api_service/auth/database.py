# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Database connection and session management for SQLite via SQLAlchemy."""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""


# Database file location — persistent across Docker restarts via volume mount
DATA_DIR = Path(os.getenv("GRAPHRAG_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR / 'graphrag_auth.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """FastAPI dependency that yields a database session.

    Usage:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()
