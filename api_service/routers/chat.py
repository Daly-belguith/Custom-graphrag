# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Conversational AI Chat router with multi-turn context."""

import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import ChatMessage, UsageLog, User
from api_service.auth.security import get_current_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    
    
class ChatResponse(BaseModel):
    response: str
    search_type_used: str


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to the AI and get a response based on the knowledge graph."""
    start_time = time.time()
    
    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=req.message
    )
    db.add(user_msg)
    
    # In a real implementation:
    # 1. Fetch recent history from DB
    # 2. Use an LLM to decide whether this is a local or global search
    # 3. Execute the search
    # 4. Stream response back
    
    search_type = "local" # Mock decision
    response_content = f"Mock Chat Response to: '{req.message}'. (Context derived via {search_type} search)."
    
    # Save assistant message
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=response_content,
        search_type_used=search_type,
        model_used="gpt-4o-mini",
        tokens_used=400,
    )
    db.add(assistant_msg)
    
    # Log usage
    latency = time.time() - start_time
    usage = UsageLog(
        user_id=current_user.id,
        endpoint="/api/v1/chat",
        method="POST",
        search_type="chat_" + search_type,
        model_used="gpt-4o-mini",
        tokens_used=400,
        latency_ms=latency * 1000,
    )
    db.add(usage)
    
    db.commit()
    
    return ChatResponse(
        response=response_content,
        search_type_used=search_type
    )


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the user's conversation history."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
            "search_type_used": m.search_type_used
        }
        for m in messages
    ]


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear the user's conversation history."""
    db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).delete()
    db.commit()
    
    return {"message": "Chat history cleared"}
