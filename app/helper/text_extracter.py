
import io

import pdfplumber
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


async def _read_text_from_upload(file: UploadFile) -> str:
    """
    Extract text from an uploaded file.
    - If PDF -> use pdfplumber
    - Else -> treat as a text-like file and decode as UTF-8
    """
    settings = get_settings()
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file '{file.filename}' is empty.",
        )

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Uploaded file '{file.filename}' is too large "
                f"(>{settings.max_upload_bytes} bytes)."
            ),
        )

    # crude pdf detection
    is_pdf = (
        file.content_type in ["application/pdf", "application/x-pdf"]
        or (file.filename or "").lower().endswith(".pdf")
    )

    if is_pdf:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = pdf.pages[: settings.max_pdf_pages]
                pages_text = [page.extract_text() or "" for page in pages]
            text = "\n".join(pages_text).strip()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read PDF '{file.filename}': {e}",
            )
    else:
        try:
            text = content.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode '{file.filename}' as text: {e}",
            )

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No readable text found in file '{file.filename}'.",
        )

    return text
