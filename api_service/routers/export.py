# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Export center endpoints to download user knowledge graphs and logs."""

from fastapi import APIRouter, Depends
from api_service.auth.models import User
from api_service.auth.security import get_current_user

router = APIRouter()


@router.get("/graph")
async def export_graph(current_user: User = Depends(get_current_user)):
    """Download full knowledge graph as JSON or GraphML."""
    return {"message": "Export functionality mock"}


@router.get("/entities")
async def export_entities(current_user: User = Depends(get_current_user)):
    """Download entities table as CSV."""
    return {"message": "Export functionality mock"}


@router.get("/relationships")
async def export_relationships(current_user: User = Depends(get_current_user)):
    """Download relationships table as CSV."""
    return {"message": "Export functionality mock"}


@router.get("/communities")
async def export_communities(current_user: User = Depends(get_current_user)):
    """Download community reports as JSON."""
    return {"message": "Export functionality mock"}


@router.get("/query-history")
async def export_query_history(current_user: User = Depends(get_current_user)):
    """Download user's query history as CSV."""
    return {"message": "Export functionality mock"}
