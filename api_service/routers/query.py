# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Query endpoints for executing searches against a user's isolated GraphRAG index."""

import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api_service.auth.database import get_db
from api_service.auth.models import UsageLog, User
from api_service.auth.security import get_current_user

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    stream: bool = False
    
    
class QueryResponse(BaseModel):
    response: str
    context_data: dict | None = None
    completion_time: float


def log_query_usage(db: Session, user_id: str, search_type: str, query_text: str, latency: float):
    """Helper to log query usage for billing/tracking."""
    # In a real implementation, we would extract the actual model and tokens from the LiteLLM response
    usage = UsageLog(
        user_id=user_id,
        endpoint=f"/api/v1/query/{search_type}",
        method="POST",
        search_type=search_type,
        model_used="gpt-4o-mini",  # Mocked
        tokens_used=len(query_text) * 2 + 500,  # Mocked
        latency_ms=latency * 1000,
    )
    db.add(usage)
    db.commit()


@router.post("/local", response_model=QueryResponse)
async def local_search(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a Local Search against the user's index."""
    start_time = time.time()
    
    # Mock implementation - in reality this would initialize graphrag.query.local_search.LocalSearch
    # and pass it the data from output/users/{current_user.id}/
    
    latency = time.time() - start_time
    log_query_usage(db, current_user.id, "local", req.query, latency)
    
    return QueryResponse(
        response=f"Mock Local Search Response for query: '{req.query}'. This data comes from user {current_user.id}'s isolated index.",
        completion_time=latency
    )


@router.post("/global", response_model=QueryResponse)
async def global_search(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a Global Map-Reduce Search against the user's index."""
    start_time = time.time()
    
    latency = time.time() - start_time
    log_query_usage(db, current_user.id, "global", req.query, latency)
    
    return QueryResponse(
        response=f"Mock Global Search Response for query: '{req.query}'. Synthesizing broad themes across the dataset.",
        completion_time=latency
    )


@router.post("/drift", response_model=QueryResponse)
async def drift_search(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a Drift Search against the user's index."""
    start_time = time.time()
    
    latency = time.time() - start_time
    log_query_usage(db, current_user.id, "drift", req.query, latency)
    
    return QueryResponse(
        response=f"Mock Drift Search Response for query: '{req.query}'.",
        completion_time=latency
    )


@router.post("/basic", response_model=QueryResponse)
async def basic_search(
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a Basic Vector Search against the user's index."""
    start_time = time.time()
    
    latency = time.time() - start_time
    log_query_usage(db, current_user.id, "basic", req.query, latency)
    
    return QueryResponse(
        response=f"Mock Basic Search Response for query: '{req.query}'.",
        completion_time=latency
    )
