import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    """
    Central application settings.

    These values are read from environment variables once at startup and then
    cached. If required values are missing, the application will fail fast
    with a clear error instead of crashing later at import time.
    """

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the Ollama server.",
    )
    ollama_default_model: str = Field(
        default="qwen3:1.7b",
        description="Default Ollama model name.",
    )

    # Embeddings
    embed_model_name: str = Field(
        ...,
        description="SentenceTransformer embedding model name.",
    )

    # Input limits
    max_jd_chars: int = Field(
        default=8000,
        ge=1,
        description="Maximum number of characters allowed for JD text.",
    )
    max_resume_chars: int = Field(
        default=20000,
        ge=1,
        description="Maximum number of characters allowed for resume text.",
    )
    max_upload_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5MB
        ge=1,
        description="Maximum size in bytes for uploaded files.",
    )
    max_pdf_pages: int = Field(
        default=20,
        ge=1,
        description="Maximum number of pages to read from PDFs.",
    )
    max_questions_per_category: int = Field(
        default=25,
        ge=1,
        description="Maximum number of JD questions per category.",
    )

    # Auth / security
    api_key: str | None = Field(
        default=None,
        description="Optional API key required for accessing protected endpoints.",
    )
    max_requests_per_minute: int | None = Field(
        default=30,
        ge=1,
        description="Soft per-client rate limit for scoring requests.",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Load settings from environment once and cache them.
    Raises a clear error if required values are missing or invalid.
    """
    # Required: EMBED_MODEL_NAME
    embed_model_name: Optional[str] = os.getenv("EMBED_MODEL_NAME")
    if not embed_model_name:
        raise RuntimeError(
            "EMBED_MODEL_NAME environment variable is required but not set. "
            "Configure it to point to a valid SentenceTransformer model."
        )

    try:
        settings = Settings(
            embed_model_name=embed_model_name,
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3:1.7b"),
        )
    except ValidationError as exc:
        raise RuntimeError(f"Invalid application settings: {exc}") from exc

    return settings
