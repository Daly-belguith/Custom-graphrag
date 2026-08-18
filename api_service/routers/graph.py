# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Graph visualization and data extraction router."""

from fastapi import APIRouter, Depends, HTTPException
from api_service.auth.models import User
from api_service.auth.security import get_current_user

router = APIRouter()


@router.get("/entities")
async def get_graph_entities(current_user: User = Depends(get_current_user)):
    """Return list of extracted entities from user's index."""
    # Mock data from Parquet
    return {"entities": [{"id": "E1", "label": "MockEntity"}]}


@router.get("/relationships")
async def get_graph_relationships(current_user: User = Depends(get_current_user)):
    """Return list of relationships from user's index."""
    # Mock data from Parquet
    return {"relationships": [{"source": "E1", "target": "E2", "type": "MockRel"}]}


@router.get("/communities")
async def get_graph_communities(current_user: User = Depends(get_current_user)):
    """Return community summaries with hierarchy levels."""
    return {"communities": []}


@router.get("/visualize")
async def get_graph_visualize(current_user: User = Depends(get_current_user)):
    """Return a JSON graph structure formatted for D3.js/Cytoscape.js."""
    return {
        "nodes": [{"data": {"id": "n1", "label": "Node 1"}}],
        "edges": [{"data": {"source": "n1", "target": "n2", "label": "Connected"}}]
    }
