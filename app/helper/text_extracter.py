
import io
from fastapi import HTTPException, UploadFile, status
import pdfplumber


async def _read_text_from_upload(file: UploadFile) -> str:
    """
    Extract text from an uploaded file.
    - If PDF -> use pdfplumber
    - Else -> treat as a text-like file and decode as UTF-8
    """
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file '{file.filename}' is empty.",
        )

    # crude pdf detection
    is_pdf = (
        file.content_type in ["application/pdf", "application/x-pdf"]
        or (file.filename or "").lower().endswith(".pdf")
    )

    if is_pdf:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
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
