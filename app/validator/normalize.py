from typing import Optional

from fastapi import File, Form, HTTPException, UploadFile, status

from app.config import get_settings
from app.helper.text_extracter import _read_text_from_upload
from app.schemas.score_input_schema import NormalizedScoreInput
from app.validator.scoring_validators import _ensure_exactly_one


async def normalize_score_input(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
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
    settings = get_settings()

    _ensure_exactly_one("jd", jd_text, jd_file)
    _ensure_exactly_one("resume", resume_text, resume_file)

    if jd_file is not None:
        jd_content = await _read_text_from_upload(jd_file)
    else:
        jd_content = (jd_text or "").strip()
        if not jd_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="jd_text is empty.",
            )
        if len(jd_content) > settings.max_jd_chars:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"jd_text is too long "
                    f"(>{settings.max_jd_chars} characters)."
                ),
            )

    if resume_file is not None:
        resume_content = await _read_text_from_upload(resume_file)
    else:
        resume_content = (resume_text or "").strip()
        if not resume_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resume_text is empty.",
            )
        if len(resume_content) > settings.max_resume_chars:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    "resume_text is too long "
                    f"(>{settings.max_resume_chars} characters)."
                ),
            )

    return NormalizedScoreInput(jd=jd_content, resume=resume_content)
