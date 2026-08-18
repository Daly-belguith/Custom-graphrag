# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Health check and system status router."""

import time
from typing import Any

from fastapi import APIRouter

router = APIRouter()

# Record startup time for uptime calculation
START_TIME = time.time()


@router.get("/health", tags=["System"])
async def get_health() -> dict[str, Any]:
    """Public health check endpoint.
    
    Used by Docker healthchecks and VPS monitoring to verify the service is running.
    """
    uptime_seconds = int(time.time() - START_TIME)
    
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
    }
