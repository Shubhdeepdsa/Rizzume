from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel

from app.helper.text_extracter import _read_text_from_upload
from app.validator.scoring_validators import _ensure_exactly_one

router = APIRouter()


@router.get("/score/health")
async def score_root():
    return {"status": "scoring running"}


class NormalizedScoreInput(BaseModel):
    jd: str
    resume: str


async def normalize_score_input(
    # JD: text or file
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),

    # Resume: text or file
    resume_text: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
) -> NormalizedScoreInput:
    """
    Both JD and Resume are required.
    For each of them, you can send either:
      - *_text
      - OR *_file (PDF / text)
    But not both for the same one.
    """

    # 1. Enforce exactly one per side
    _ensure_exactly_one("jd", jd_text, jd_file)
    _ensure_exactly_one("resume", resume_text, resume_file)

    # 2. Normalize JD
    if jd_file is not None:
        jd_content = await _read_text_from_upload(jd_file)
    else:
        jd_content = (jd_text or "").strip()
        if not jd_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="jd_text is empty.",
            )

    # 3. Normalize Resume
    if resume_file is not None:
        resume_content = await _read_text_from_upload(resume_file)
    else:
        resume_content = (resume_text or "").strip()
        if not resume_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resume_text is empty.",
            )

    return NormalizedScoreInput(jd=jd_content, resume=resume_content)


@router.post("/score")
async def score_resume(payload: NormalizedScoreInput = Depends(normalize_score_input)):
    """
    JD and Resume are BOTH REQUIRED.

    Contract (multipart/form-data):

      - To send files:
            jd_file: UploadFile (PDF / text)
            resume_file: UploadFile (PDF / text)

      - To send raw text:
            jd_text: string
            resume_text: string

    Exactly one of *_text or *_file must be provided for each of JD and Resume.
    """

    jd_text = payload.jd
    resume_text = payload.resume

    # TODO: Plug in your deterministic scoring logic here
    #       jd_text and resume_text are now plain strings.

    dummy_score = 0.0

    return {
        "success": True,
        "score": dummy_score,
        "jd_text_length": len(jd_text),
        "resume_text_length": len(resume_text),
        "jd_preview": jd_text[:400],
        "resume_preview": resume_text[:400],
        "message": "Scoring placeholder — plug your LLM logic here.",
    }
