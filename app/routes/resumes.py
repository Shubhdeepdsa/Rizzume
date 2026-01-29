import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from pydantic import ValidationError

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
    # 1. Parse Tags
    try:
        tag_list = json.loads(tags)
        if not isinstance(tag_list, list):
            tag_list = []
    except json.JSONDecodeError:
        tag_list = []

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
            tags=tag_list,
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
