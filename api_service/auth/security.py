# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Security utilities: password hashing, JWT tokens, API key verification, role dependencies."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import APIToken, User

# --- Password Hashing ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT Token Management ---

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production-please")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def create_jwt_token(user_id: str, role: str) -> str:
    """Create a JWT token for frontend session authentication.

    Args:
        user_id: The user's unique ID.
        role: The user's role (superadmin | user).

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string.

    Returns:
        The decoded payload dict with 'sub' and 'role' keys.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- API Key Generation ---

def generate_api_key() -> str:
    """Generate a cryptographically secure API key (64 hex characters)."""
    return secrets.token_hex(32)


# --- Authentication Dependencies ---

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to resolve the current authenticated user.

    Supports two authentication methods:
    1. JWT Bearer token (from frontend login)
    2. API Key (for programmatic REST access)

    Args:
        credentials: The Bearer token from the Authorization header.
        db: Database session.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException: 401 if no valid credentials provided.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try JWT first
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
            if user:
                return user
    except JWTError:
        pass

    # Try API Key
    api_token = db.query(APIToken).filter(
        APIToken.token_key == token,
        APIToken.is_active == True,  # noqa: E712
    ).first()
    if api_token:
        # Check expiration
        if api_token.expires_at and api_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
            )
        user = db.query(User).filter(User.id == api_token.user_id, User.is_active == True).first()  # noqa: E712
        if user:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """FastAPI dependency that requires the current user to have superadmin role.

    Args:
        current_user: The authenticated user.

    Returns:
        The user if they are a superadmin.

    Raises:
        HTTPException: 403 if the user is not a superadmin.
    """
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required",
        )
    return current_user
