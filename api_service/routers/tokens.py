# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""API token management router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import APIToken, User
from api_service.auth.security import generate_api_key, get_current_user

router = APIRouter()


@router.get("/my-token")
async def get_my_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the current user's API token."""
    token = db.query(APIToken).filter(APIToken.user_id == current_user.id).first()
    if not token:
        # Should not happen as a token is created with the user, but just in case
        raise HTTPException(status_code=404, detail="Token not found")
        
    return {
        "token_key": token.token_key,
        "created_at": token.created_at,
        "expires_at": token.expires_at,
    }


@router.post("/regen")
async def regenerate_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate the current user's API token (invalidates the old one)."""
    token = db.query(APIToken).filter(APIToken.user_id == current_user.id).first()
    if not token:
        # Create one if missing
        token = APIToken(user_id=current_user.id)
        db.add(token)
        
    token.token_key = generate_api_key()
    db.commit()
    
    return {
        "message": "Token regenerated successfully",
        "token_key": token.token_key,
    }
