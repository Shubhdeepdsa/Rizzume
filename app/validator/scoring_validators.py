from typing import Optional
from fastapi import HTTPException, UploadFile, status

def _ensure_exactly_one(
    label: str,
    text_value: Optional[str],
    file_value: Optional[UploadFile],
):
    """
    Enforce:
      - You MUST provide this entity (JD or resume)
      - You MUST NOT provide both text and file for the same entity
    """
    if text_value and file_value:
        # both present -> not allowed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label}: provide either {label}_text OR {label}_file, not both.",
        )
    if not text_value and not file_value:
        # both missing -> not allowed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} is required. Provide {label}_text or {label}_file.",
        )
