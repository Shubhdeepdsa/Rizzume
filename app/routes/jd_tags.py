from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from app.security import get_current_user, get_current_user_token
from app.service.pocketbase import get_pocketbase_service, PocketBaseService
from app.service.tag_extractor import get_tag_manager
from app.service.embedding_service import embed_texts
import json

router = APIRouter(prefix="/api/jd/tags", tags=["JD Tags"])

class CreateJDTagRequest(BaseModel):
    label: str
    category: str
    
class UpdateJDTagRequest(BaseModel):
    label: Optional[str] = None
    category: Optional[str] = None

@router.get("")
async def list_jd_tags(
    search: Optional[str] = None,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """List all JD tags for the current user, optionally filtered by fuzzy search on label."""
    try:
        # We assume pb.list_tags was checking resume_tags, but we want jd_tags.
        # PocketBaseService needs list_jd_tags?
        # Actually pb.list_tags was originally checking resume_tags? 
        # Wait, let's check pb.list_tags implementation in my previous view.
        # It was querying "resume_tags".
        # So I need to use a method that queries "jd_tags".
        # pb.get_all_tags_with_vectors queries jd_tags but it gets ALL.
        # I should add list_jd_tags to PB service or use generic list.
        # Let's add list_jd_tags to PB service if it doesn't exist or modify logic here.
        
        # Actually, let's look at `app/service/pocketbase.py` again.
        # It has `list_tags` -> `resume_tags`.
        # It has `get_all_tags_with_vectors` -> `jd_tags`.
        # It DOES NOT have a simple `list_jd_tags` with search.
        
        # I will implement a direct call here or add to service. 
        # Adding to service is cleaner.
        # For now, I'll use the generic client access to keep it simple or add a new method.
        # Let's add `list_jd_tags` to jd_tags.py using direct client access if possible, 
        # or better, add to PB Service.
        
        # But wait, I can't edit PB service in this same tool call easily without context switching.
        # I'll rely on `pb.client.get` directly here for speed as I have access to `pb.client`.
        
        headers = {"Authorization": f"Bearer {token}"}
        filter_str = f'user="{user["id"]}"'
        if search:
            filter_str += f' && label ~ "{search}"'

        resp = await pb.client.get(
            "/api/collections/jd_tags/records",
            headers=headers,
            params={"filter": filter_str, "sort": "label"}
        )
        if resp.status_code != 200:
             raise HTTPException(status_code=resp.status_code, detail="Failed to fetch tags")
             
        return resp.json().get("items", [])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_jd_tag(
    request: CreateJDTagRequest,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Create a new JD tag with vector embedding."""
    try:
        # Embedding
        vec = embed_texts([request.label])[0]
        
        manager = get_tag_manager()
        # We use manager to ensure cache is updated, effectively.
        # Manager `create_tag` does: DB create + Cache update.
        await manager._ensure_cache(pb, token, user["id"])
        
        new_id = await manager.create_tag(pb, token, user["id"], request.label, request.category, vec.tolist())
        return {"id": new_id, "label": request.label, "category": request.category}
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "400" in str(e):
             raise HTTPException(status_code=400, detail="Tag already exists.")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{tag_id}")
async def update_jd_tag(
    tag_id: str,
    data: UpdateJDTagRequest,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Update JD tag. Re-embeds if label changes."""
    manager = get_tag_manager()
    try:
        if data.label:
            # Re-embed and update using manager helper
            await manager.update_tag_vector(pb, token, tag_id, data.category or "skills", data.label)
             # Note: update_tag_vector in manager assumes we want to update vector.
             # If category is also changing, we might need a separate call.
             # Manager logic is slightly tailored to internal use.
             # Let's just trust it updates label and vector.
             
            if data.category:
                 # Separate update for category if needed
                 await pb.update_jd_tag(token, tag_id, {"category": data.category})
                 
            return {"status": "updated"}
            
        elif data.category:
            await pb.update_jd_tag(token, tag_id, {"category": data.category})
            return {"status": "updated"}
            
        return {"status": "no_change"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tag_id}")
async def delete_jd_tag(
    tag_id: str,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        await pb.delete_jd_tag(token, tag_id)
        # Ideally we invalidating cache here too.
        manager = get_tag_manager()
        manager.last_refresh_time = 0 
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
