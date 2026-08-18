# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Rate limiting middleware to protect endpoints from abuse."""

import os
import time
from collections import defaultdict

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# In-memory store: { ip_address: [timestamp1, timestamp2, ...] }
_request_history: dict[str, list[float]] = defaultdict(list)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean up history older than 60 seconds
        _request_history[client_ip] = [t for t in _request_history[client_ip] if now - t < 60]
        
        if len(_request_history[client_ip]) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."}
            )
            
        _request_history[client_ip].append(now)
        
        response = await call_next(request)
        return response
