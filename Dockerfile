# Use Python 3.11 slim image
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY packages/ packages/
COPY api_service/ api_service/
COPY frontend/ frontend/

# Install workspace sub-packages and API dependencies
RUN uv pip install --system ./packages/*
RUN uv pip install --system fastapi uvicorn python-jose[cryptography] passlib[bcrypt] "bcrypt<4.0.0" pydantic[email] python-multipart sqlalchemy

# Expose FastAPI port
EXPOSE 8000

# Healthcheck targeting the health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start the uvicorn server
CMD ["uvicorn", "api_service.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
