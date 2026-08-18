# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""FastAPI application initialization and server configuration."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api_service.auth.database import init_db, SessionLocal
from api_service.auth.seed import seed_superadmin
from api_service.middleware.rate_limiter import RateLimiterMiddleware
from api_service.routers import (
    auth, chat, documents, export, graph, health, 
    indexing, notifications, prompts, query, settings, tokens, usage, users
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    logger.info("Starting up FastAPI application...")
    
    # Initialize database tables
    init_db()
    
    # Seed superadmin account if necessary
    with SessionLocal() as db:
        seed_superadmin(db)
        
    yield
    
    logger.info("Shutting down FastAPI application...")


app = FastAPI(
    title="GraphRAG Platform API",
    description="Multi-tenant API platform for Custom GraphRAG with Role-Based Access Control.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # We will secure this later if needed
    redoc_url=None,
)

# Configure Middleware
app.add_middleware(RateLimiterMiddleware)

# Configure CORS
# In production, origins should be restricted via environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(tokens.router, prefix="/api/v1/tokens", tags=["API Tokens"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(indexing.router, prefix="/api/v1/indexing", tags=["Indexing"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(query.router, prefix="/api/v1/query", tags=["Query Execution"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["Prompts"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(usage.router, prefix="/api/v1/usage", tags=["Usage Tracking"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph Visualization"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])

# Serve frontend static files (create dir to prevent startup error)
import os
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
