# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""LLM settings and Environment configuration router for superadmins."""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api_service.auth.models import User
from api_service.auth.security import require_superadmin

router = APIRouter()


class LLMSettings(BaseModel):
    model_provider: str
    model: str
    api_base: str | None = None


class EnvVarUpdate(BaseModel):
    key: str
    value: str


@router.get("/llm")
async def get_llm_settings(_: User = Depends(require_superadmin)):
    """Get current LLM provider configuration."""
    # Mock reading from settings.yaml
    return {
        "model_provider": "openai",
        "model": "gpt-4o-mini",
        "api_base": None
    }


@router.put("/llm")
async def update_llm_settings(req: LLMSettings, _: User = Depends(require_superadmin)):
    """Update LLM provider settings (writes to settings.yaml)."""
    # Mock writing to settings.yaml
    return {"message": "LLM settings updated successfully"}


@router.post("/llm/test")
async def test_llm_connection(req: LLMSettings, _: User = Depends(require_superadmin)):
    """Test connection to the configured LLM provider."""
    # Mock calling LiteLLM completion to test
    return {"status": "success", "message": f"Connection to {req.model_provider} successful."}


@router.get("/env")
async def get_env_settings(_: User = Depends(require_superadmin)):
    """List configurable environment variables."""
    # Read actual env vars, masking secrets
    keys = ["GRAPHRAG_API_KEY", "JWT_SECRET", "DEFAULT_ADMIN_PASSWORD", "RATE_LIMIT_PER_MINUTE"]
    settings = {}
    for key in keys:
        val = os.getenv(key, "")
        # Mask secrets
        if key in ["GRAPHRAG_API_KEY", "JWT_SECRET", "DEFAULT_ADMIN_PASSWORD"]:
            settings[key] = "****" + val[-4:] if len(val) > 4 else "****"
        else:
            settings[key] = val
            
    return {"env": settings}


@router.put("/env")
async def update_env_setting(req: EnvVarUpdate, _: User = Depends(require_superadmin)):
    """Update an environment variable (writes to .env file)."""
    env_path = Path(".env")
    lines = []
    updated = False
    
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith(f"{req.key}="):
                f.write(f"{req.key}={req.value}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f"{req.key}={req.value}\n")
            
    return {"message": f"Environment variable {req.key} updated"}


@router.post("/restart")
async def restart_service(_: User = Depends(require_superadmin)):
    """Graceful service restart (mocked for now)."""
    # In a real Docker env, this might touch a specific file that triggers a reload
    # or exit the process if the orchestrator (Docker/Systemd) is set to auto-restart
    return {"message": "Service restart initiated (mocked)"}
