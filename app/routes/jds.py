from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.helper.text_extracter import read_text_from_upload
from app.security import get_current_user, get_current_user_token
from app.service.jd_question_generator import generate_jd_questions, extract_metadata_from_jd
from app.service.pocketbase import get_pocketbase_service, PocketBaseService

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
        # 2. Extract Metadata (Role/Company) - LLM
        metadata = await run_in_threadpool(extract_metadata_from_jd, final_text)
        
        # 3. Generate Questions - LLM
        questions_obj = await run_in_threadpool(generate_jd_questions, final_text)
        # Convert to list of dicts or keep structure? PB expects JSON.
        # We store the whole object as JSON.
        questions_json = questions_obj.model_dump()
        
        # 4. Store
        record = await pb.create_jd(
            token=token,
            user_id=user["id"],
            role_name=metadata["role_name"],
            company_name=metadata["company_name"],
            original_text=final_text,
            questions=questions_json,
            file_obj=file.file if file else None,
            filename=file.filename if file else None
        )
        return record

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process JD: {e}")

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
