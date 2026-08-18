# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Usage tracking and reporting router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import UsageLog, User
from api_service.auth.security import get_current_user, require_superadmin

router = APIRouter()


@router.get("/me")
async def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for the current user."""
    # Total queries
    total_queries = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id
    ).count()
    
    # Total tokens
    total_tokens = db.query(func.sum(UsageLog.tokens_used)).filter(
        UsageLog.user_id == current_user.id
    ).scalar() or 0
    
    return {
        "user_id": current_user.id,
        "total_queries": total_queries,
        "total_tokens_consumed": total_tokens,
    }


@router.get("/users/{user_id}")
async def get_user_usage(
    user_id: str,
    _: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get usage stats for a specific user (Superadmin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    total_queries = db.query(UsageLog).filter(UsageLog.user_id == user_id).count()
    total_tokens = db.query(func.sum(UsageLog.tokens_used)).filter(UsageLog.user_id == user_id).scalar() or 0
    
    return {
        "user_id": user_id,
        "username": user.username,
        "total_queries": total_queries,
        "total_tokens_consumed": total_tokens,
    }


@router.get("/global")
async def get_global_usage(
    _: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get platform-wide usage summary (Superadmin only)."""
    total_queries = db.query(UsageLog).count()
    total_tokens = db.query(func.sum(UsageLog.tokens_used)).scalar() or 0
    
    return {
        "platform_total_queries": total_queries,
        "platform_total_tokens": total_tokens,
    }
