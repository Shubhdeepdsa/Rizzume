from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from app.security import get_current_user, get_current_user_token
from app.service.pocketbase import get_pocketbase_service, PocketBaseService

router = APIRouter(prefix="/api/tags", tags=["Tags"])

class CreateTagRequest(BaseModel):
    label: str

@router.get("")
async def list_tags(
    search: Optional[str] = None,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """List all resume tags for the current user, optionally filtered by fuzzy search."""
    try:
        items = await pb.list_tags(token, user["id"], search_query=search)
        # Return simplified list or full objects? User asked for list.
        # Let's return the full objects as they contain IDs and labels.
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_tag(
    request: CreateTagRequest,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Create a new tag."""
    try:
        tag = await pb.create_tag(token, user["id"], request.label)
        return tag
    except Exception as e:
        # PocketBase might error on unique constraint (user+label)
        # Check if error message indicates duplicate
        if "UNIQUE constraint failed" in str(e) or "400" in str(e):
             raise HTTPException(status_code=400, detail="Tag already exists or invalid.")
        raise HTTPException(status_code=500, detail=str(e))
