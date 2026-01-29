from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from app.security import get_current_user, get_current_user_token
from app.service.pocketbase import get_pocketbase_service, PocketBaseService

router = APIRouter(prefix="/api/resume/tags", tags=["Resume Tags"])

class CreateTagRequest(BaseModel):
    label: str
    
class UpdateTagRequest(BaseModel):
    label: Optional[str] = None

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
    """Create a new resume tag."""
    try:
        # Create simple resume tag (no vector, no category)
        record = await pb.create_tag(token, user["id"], request.label)
        return record
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "400" in str(e):
             raise HTTPException(status_code=400, detail="Tag already exists or invalid.")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{tag_id}")
async def update_tag(
    tag_id: str,
    data: UpdateTagRequest,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """
    Update a resume tag. Only label update is supported for resume tags.
    """
    try:
        if data.label:
            await pb.update_resume_tag(token, tag_id, data.label)
            return {"status": "updated", "detail": "Label updated"}
            
        return {"status": "no_change"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: str,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        await pb.delete_resume_tag(token, tag_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
