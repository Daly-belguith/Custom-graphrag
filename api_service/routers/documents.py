# Copyright (c) 2024 Custom GraphRAG.
# Licensed under the MIT License

"""Document management router with isolation per user."""

import os
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from api_service.auth.models import User
from api_service.auth.security import get_current_user

router = APIRouter()


def get_user_input_dir(user_id: str) -> Path:
    """Helper to get the isolated input directory for a user."""
    input_dir = Path("input") / "users" / user_id
    # Ensure it exists (it should have been created on user creation)
    input_dir.mkdir(parents=True, exist_ok=True)
    return input_dir


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a document to the user's isolated input directory."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
        
    # Validate extension
    allowed_extensions = {".txt", ".csv", ".json"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension {ext}")
        
    input_dir = get_user_input_dir(current_user.id)
    file_path = input_dir / file.filename
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    return {"message": "File uploaded successfully", "filename": file.filename}


@router.get("/")
async def list_documents(
    user_id: str | None = None,
    current_user: User = Depends(get_current_user)
):
    """List documents.
    
    Regular users see their own. Superadmins can pass `user_id` to view others.
    """
    target_user_id = current_user.id
    
    if user_id:
        if current_user.role != "superadmin" and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot list another user's documents")
        target_user_id = user_id
        
    input_dir = get_user_input_dir(target_user_id)
    files = []
    
    if input_dir.exists():
        for file_path in input_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
                
    return {"documents": files}


@router.delete("/{filename}")
async def delete_document(
    filename: str,
    user_id: str | None = None,
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    # Prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    target_user_id = current_user.id
    
    if user_id:
        if current_user.role != "superadmin" and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot delete another user's document")
        target_user_id = user_id
        
    input_dir = get_user_input_dir(target_user_id)
    file_path = input_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
        
    return {"message": "File deleted successfully"}
