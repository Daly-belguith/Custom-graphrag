# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Auto-seed initial superadmin account and per-user directory structure."""

import logging
import os
from pathlib import Path

from sqlalchemy.orm import Session

from api_service.auth.models import APIToken, User
from api_service.auth.security import generate_api_key, hash_password

logger = logging.getLogger(__name__)


def seed_superadmin(db: Session) -> None:
    """Create the initial superadmin account if no users exist.

    Credentials come from environment variables:
    - DEFAULT_ADMIN_USERNAME (default: "admin")
    - DEFAULT_ADMIN_PASSWORD (default: "admin123")
    - DEFAULT_ADMIN_EMAIL (default: "admin@graphrag.local")

    Also creates a default API token for the superadmin.
    """
    existing_users = db.query(User).count()
    if existing_users > 0:
        logger.info("Database already has users, skipping superadmin seeding.")
        return

    username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@graphrag.local")

    superadmin = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role="superadmin",
        is_active=True,
    )
    db.add(superadmin)
    db.flush()  # Get the generated ID

    # Create default API token for superadmin
    api_token = APIToken(
        user_id=superadmin.id,
        token_key=generate_api_key(),
    )
    db.add(api_token)

    # Create per-user directory structure
    create_user_directories(superadmin.id)

    db.commit()
    logger.info(
        "Superadmin account seeded: username='%s', email='%s'",
        username, email,
    )


def create_user_directories(user_id: str) -> None:
    """Create the isolated directory structure for a user.

    Creates:
    - input/users/{user_id}/      (raw documents)
    - output/users/{user_id}/     (Parquet graph output & LanceDB vectors)
    - cache/users/{user_id}/      (indexing pipeline cache)

    Args:
        user_id: The user's unique ID.
    """
    base_dirs = [
        Path("input") / "users" / user_id,
        Path("output") / "users" / user_id,
        Path("cache") / "users" / user_id,
    ]
    for dir_path in base_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug("Created directory: %s", dir_path)
