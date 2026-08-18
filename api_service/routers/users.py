# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""User management router (CRUD operations for superadmins)."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import APIToken, User
from api_service.auth.security import generate_api_key, get_current_user, hash_password, require_superadmin
from api_service.auth.seed import create_user_directories

router = APIRouter()


class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None
    role: str = "user"


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None


@router.get("/")
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin)
) -> list[dict[str, Any]]:
    """List all users (Superadmin only)."""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin)
):
    """Create a new user (Superadmin only)."""
    # Check if username exists
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Check if email exists
    if req.email:
        existing_email = db.query(User).filter(User.email == req.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ["user", "superadmin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    new_user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
    )
    db.add(new_user)
    db.flush()  # To get the ID
    
    # Create API token for new user
    api_token = APIToken(
        user_id=new_user.id,
        token_key=generate_api_key(),
    )
    db.add(api_token)
    
    # Create directory structure
    create_user_directories(new_user.id)
    
    db.commit()
    
    return {"message": "User created successfully", "user_id": new_user.id}


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin)
):
    """Get user details by ID (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    req: UserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin)
):
    """Update user role, status, or password (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if req.role is not None:
        if req.role not in ["user", "superadmin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = req.role
        
    if req.is_active is not None:
        user.is_active = req.is_active
        
    if req.password is not None:
        user.hashed_password = hash_password(req.password)
        
    db.commit()
    return {"message": "User updated successfully"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Delete user and all associated data (Superadmin only)."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    
    # Note: the physical directory structure is intentionally left on disk 
    # to prevent accidental complete data loss. An admin could choose to delete 
    # the directories manually or via a separate cleanup script.
    
    return {"message": "User deleted successfully"}
