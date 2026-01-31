import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from pydantic import ValidationError, BaseModel

from app.helper.text_extracter import read_text_from_upload
from app.security import get_current_user, get_current_user_token
from app.service.pocketbase import get_pocketbase_service, PocketBaseService
from app.service.resume_rag_scorer import build_resume_index

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

@router.post("")
async def upload_resume(
    file: UploadFile = File(...),
    tags: str = Form("[]"),  # JSON string list of tags
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    # 1. Parse Tag IDs
    try:
        if tags.strip().startswith("["):
            tag_ids = json.loads(tags)
            if not isinstance(tag_ids, list):
                 tag_ids = []
        else:
             # Handle comma-separated list
             tag_ids = [t.strip() for t in tags.split(",") if t.strip()]
    except json.JSONDecodeError:
        # Fallback to comma split if it looked like JSON but failed? 
        # Or just empty.
        # Actually simplest is: try json, if fail (or not list), try split.
        tag_ids = []
        if "," in tags or not tags.startswith("["):
             tag_ids = [t.strip() for t in tags.split(",") if t.strip()]


    # 2. Extract Text
    try:
        text_content = await read_text_from_upload(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Vectorize (Smart Caching)
    # Returns chunks (TextChunk objects) and embeddings (numpy array)
    try:
        chunks, embeddings_np = build_resume_index(text_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vectorization failed: {e}")

    # 4. Serialize Embeddings for Storage
    # We store a list of dicts: {text, start, end, vector: []}
    serialized_embeddings = []
    for i, chunk in enumerate(chunks):
        vector = embeddings_np[i].tolist()
        serialized_embeddings.append({
            "id": chunk.id,
            "start": chunk.start,
            "end": chunk.end,
            "text": chunk.text,
            "vector": vector
        })

    # 5. Store in Pocketbase
    # Reset file cursor for upload
    await file.seek(0)
    
    try:
        record = await pb.create_resume(
            token=token,
            user_id=user["id"],
            name=file.filename or "Untitled Resume",
            original_text=text_content,
            file_obj=file.file,
            filename=file.filename,
            tags=tag_ids,
            embeddings=serialized_embeddings
        )
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {e}")

@router.get("")
async def list_resumes(
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        items = await pb.list_resumes(token, user["id"])
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{resume_id}")
async def update_tags(
    resume_id: str,
    tags: List[str],
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        record = await pb.update_resume_tags(token, resume_id, tags)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResumeFilter(BaseModel):
    tags: Optional[List[str]] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    name_contains: Optional[str] = None

@router.post("/search")
async def search_resumes(
    filter_data: ResumeFilter,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        # Convert pydantic model to dict, excluding None values
        criteria = filter_data.model_dump(exclude_none=True)
        items = await pb.search_resumes(token, user["id"], criteria)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        # 1. Get Resume metadata to find filename
        resume = await pb.get_resume(token, resume_id)
        # PB stores file in 'file' field usually
        filename = resume.get("file")
        if not filename:
             raise HTTPException(status_code=404, detail="No file attached to this resume.")

        # 2. Get stream
        # collection name is 'resumes'
        stream_resp = await pb.get_file_stream(token, "resumes", resume_id, filename)
        
        if stream_resp.status_code != 200:
            error_text = await stream_resp.aread()
            await stream_resp.aclose()
            print(f"PB File Error: {stream_resp.status_code} {error_text}")
            raise HTTPException(status_code=stream_resp.status_code, detail=f"PocketBase File Error: {error_text.decode('utf-8')}")

        # 3. Stream back
        return StreamingResponse(
            stream_resp.aiter_bytes(),
            media_type=stream_resp.headers.get("content-type", "application/octet-stream"),
            headers={
                "Content-Disposition": f'inline; filename="{filename}"'
            },
            background=BackgroundTask(stream_resp.aclose)
        )
    except Exception as e:
         print(f"Download failed: {repr(e)}")
         raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")
