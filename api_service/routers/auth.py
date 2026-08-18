# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Authentication router for login and user profile retrieval."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import User
from api_service.auth.security import create_jwt_token, get_current_user, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


@router.post("/login", response_model=LoginResponse)
async def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    user = db.query(User).filter(User.username == login_req.username).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_jwt_token(user_id=user.id, role=user.role)
    
    return LoginResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the current authenticated user's profile."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at,
    }
