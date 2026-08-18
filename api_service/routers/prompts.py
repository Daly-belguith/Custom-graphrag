# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Prompt management router for superadmins."""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api_service.auth.models import User
from api_service.auth.security import require_superadmin

router = APIRouter()

PROMPTS_DIR = Path("prompts")
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


class PromptUpdate(BaseModel):
    content: str


@router.get("/")
async def list_prompts(_: User = Depends(require_superadmin)):
    """List all system prompts with a short preview."""
    prompts = []
    if PROMPTS_DIR.exists():
        for file_path in PROMPTS_DIR.glob("*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    prompts.append({
                        "name": file_path.stem,
                        "filename": file_path.name,
                        "preview": content[:200] + "..." if len(content) > 200 else content,
                    })
            except Exception:
                pass
                
    return {"prompts": prompts}


@router.get("/{name}")
async def get_prompt(name: str, _: User = Depends(require_superadmin)):
    """Read the full content of a specific prompt."""
    file_path = PROMPTS_DIR / f"{name}.txt"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"name": name, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{name}")
async def update_prompt(name: str, req: PromptUpdate, _: User = Depends(require_superadmin)):
    """Update a specific prompt's content."""
    # Prevent directory traversal
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid prompt name")
        
    file_path = PROMPTS_DIR / f"{name}.txt"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"message": "Prompt updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/reset")
async def reset_prompt(name: str, _: User = Depends(require_superadmin)):
    """Reset a prompt to its original default."""
    # Prevent directory traversal
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid prompt name")
        
    file_path = PROMPTS_DIR / f"{name}.txt"
    
    # In a real implementation, we would copy the default from graphrag package
    # For now, if we delete the file, the indexer will usually fall back to defaults
    if file_path.exists():
        file_path.unlink()
        
    return {"message": f"Prompt '{name}' reset to default"}
