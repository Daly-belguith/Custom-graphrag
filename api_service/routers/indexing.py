# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Indexing workflows and status polling."""

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import Notification, User, UsageLog
from api_service.auth.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for task status tracking for this MVP.
# In production, use Redis/Celery or a proper task queue table.
TASKS: dict[str, dict[str, Any]] = {}


class IndexingStartResponse(BaseModel):
    task_id: str
    message: str


async def mock_indexing_task(user_id: str, task_id: str, db: Session):
    """A simulated background task for indexing.
    
    In a real implementation, this would invoke the GraphRAG indexing pipeline
    passing the user's input/output/cache directories.
    """
    try:
        logger.info(f"Starting background indexing for user {user_id}, task {task_id}")
        TASKS[task_id]["status"] = "running"
        TASKS[task_id]["logs"].append("Initializing indexing pipeline...")
        
        await asyncio.sleep(2)
        TASKS[task_id]["logs"].append("Extracting entities...")
        
        await asyncio.sleep(2)
        TASKS[task_id]["logs"].append("Building knowledge graph...")
        
        await asyncio.sleep(2)
        TASKS[task_id]["logs"].append("Generating community reports...")
        
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["logs"].append("Indexing completed successfully.")
        
        # Log usage
        usage_log = UsageLog(
            user_id=user_id,
            endpoint="/api/v1/indexing/start",
            method="POST",
            tokens_used=15000,  # Simulated token usage
        )
        db.add(usage_log)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            message="Your documents have been successfully indexed. The knowledge graph is ready.",
            notification_type="success"
        )
        db.add(notification)
        db.commit()
        
    except Exception as e:
        logger.error(f"Indexing task {task_id} failed: {e}")
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["logs"].append(f"Error: {str(e)}")
        
        notification = Notification(
            user_id=user_id,
            message="An error occurred during indexing. Please check the logs.",
            notification_type="error"
        )
        db.add(notification)
        db.commit()


@router.post("/start", response_model=IndexingStartResponse)
async def start_indexing(
    background_tasks: BackgroundTasks,
    user_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger background indexing for a user's documents."""
    target_user_id = current_user.id
    
    if user_id:
        if current_user.role != "superadmin" and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot index another user's documents")
        target_user_id = user_id
        
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "status": "pending",
        "logs": [],
        "user_id": target_user_id,
    }
    
    background_tasks.add_task(mock_indexing_task, target_user_id, task_id, db)
    
    return {"task_id": task_id, "message": "Indexing started in the background"}


@router.get("/status/{task_id}")
async def get_indexing_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Poll the status and logs of an indexing task."""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if current_user.role != "superadmin" and task["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot view another user's task")
        
    return {
        "task_id": task_id,
        "status": task["status"],
        "logs": task["logs"],
    }
