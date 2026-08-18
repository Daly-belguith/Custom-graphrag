# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Notifications router for user alerts."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import Notification, User
from api_service.auth.security import get_current_user

router = APIRouter()


@router.get("/")
async def get_notifications(
    unread_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    """Get notifications for the current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
        
    notifications = query.order_by(Notification.created_at.desc()).all()
    
    return [
        {
            "id": n.id,
            "message": n.message,
            "type": n.notification_type,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False  # noqa: E712
    ).update({"is_read": True})
    
    db.commit()
    return {"message": "All notifications marked as read"}
