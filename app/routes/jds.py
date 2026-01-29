from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Body
from fastapi.concurrency import run_in_threadpool

from app.helper.text_extracter import read_text_from_upload
from app.security import get_current_user, get_current_user_token
from app.service.jd_question_generator import generate_jd_questions, extract_metadata_from_jd
from app.service.pocketbase import get_pocketbase_service, PocketBaseService
from app.service.tag_extractor import process_jd_tags

router = APIRouter(prefix="/api/jds", tags=["Job Descriptions"])

@router.post("")
async def create_jd(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    # 1. Extract Text
    final_text = ""
    if file:
        try:
            final_text = await read_text_from_upload(file)
            # Reset cursor for upload
            await file.seek(0)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif text:
        final_text = text.strip()
    
    if not final_text:
         raise HTTPException(status_code=400, detail="JD text or file is required.")

    try:
        # 2. Extract Metadata (Role/Company) - LLM (Keep existing for Title)
        # TODO: We could merge this into the new prompt effectively, but we'll run parallel for now to be safe.
        metadata_task = run_in_threadpool(extract_metadata_from_jd, final_text)
        
        # 3. Generate Questions - LLM
        questions_task = run_in_threadpool(generate_jd_questions, final_text)
        
        # 4. Extract Tags & Logistical Metadata - NEW Service
        tags_task = process_jd_tags(pb, token, user["id"], final_text)
        
        import asyncio
        # Run them in parallel for speed
        metadata, questions_obj, (tag_ids, job_meta) = await asyncio.gather(
            metadata_task, 
            questions_task, 
            tags_task
        )

        questions_json = questions_obj.model_dump()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🏷️ [Create JD] Extracted Tags: {tag_ids}")
        
        # 5. Store with all new fields
        record = await pb.create_jd(
            token=token,
            user_id=user["id"],
            role_name=metadata["role_name"],
            company_name=metadata["company_name"],
            original_text=final_text,
            questions=questions_json,
            file_obj=file.file if file else None,
            filename=file.filename if file else None,
            # New fields from job_meta (JobMetadata pydantic model)
            job_type=job_meta.job_type,
            location_type=job_meta.location_type,
            salary_min=job_meta.salary_min,
            salary_max=job_meta.salary_max,
            currency=job_meta.currency,
            tags=tag_ids
        )
        return record

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process JD: {e}")

@router.patch("/{jd_id}")
async def update_jd(
    jd_id: str,
    data: dict = Body(...),
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """
    Update JD metadata or tags.
    Expects body like: { "job_type": "...", "tags": ["id1", "id2"] }
    """
    try:
        # Check ownership logic typically handled by PB rules, but we can double check if needed.
        # PB updateRule `user = @request.auth.id` handles it.
        record = await pb.update_jd(token, jd_id, data)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{jd_id}")
async def delete_jd(
    jd_id: str,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        success = await pb.delete_jd(token, jd_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_jds(
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    try:
        items = await pb.list_jds(token, user["id"])
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
