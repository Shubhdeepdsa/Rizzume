import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

# Load .env file for secrets
load_dotenv()


def _find_config_yaml() -> Path:
    """
    Find config.yaml by looking in the project root.
    Searches from the app directory upward.
    """
    # Start from this file's directory and go up to find config.yaml
    current = Path(__file__).parent.parent  # Go to project root
    config_path = current / "config.yaml"
    if config_path.exists():
        return config_path
    
    # Fallback: check current working directory
    cwd_config = Path.cwd() / "config.yaml"
    if cwd_config.exists():
        return cwd_config
    
    raise FileNotFoundError(
        "config.yaml not found. Please ensure it exists in the project root."
    )


def _load_yaml_config() -> dict[str, Any]:
    """Load configuration from config.yaml file."""
    config_path = _find_config_yaml()
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


class Settings(BaseModel):
    """
    Central application settings.

    Configuration is loaded from config.yaml for most values.
    Sensitive values (API keys) are loaded from environment variables.
    The get_settings() function caches the result after first load.
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

    # Scoring weights
    mandatory_question_weight: float = Field(
        default=2.0,
        ge=1.0,
        description="Weight multiplier for mandatory questions in weighted average.",
    )
    optional_question_weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Weight for optional questions in weighted average.",
    )
    mandatory_cap_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How much mandatory performance affects final score cap (0=no effect, 1=full effect).",
    )

    # Auth / security (from environment only)
    api_key: str | None = Field(
        default=None,
        description="Optional API key required for accessing protected endpoints.",
    )
    max_requests_per_minute: int | None = Field(
        default=30,
        ge=1,
        description="Soft per-client rate limit for scoring requests.",
    )

    # LLM Provider Configuration
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider to use: 'ollama' or 'groq'.",
    )
    groq_api_key: str | None = Field(
        default=None,
        description="API key for Groq (required when llm_provider is 'groq').",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Model name for Groq.",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Load settings from config.yaml and environment variables, then cache them.
    
    Configuration priority:
    1. config.yaml - for all non-secret settings
    2. Environment variables - for secrets (GROQ_API_KEY, API_KEY)
    
    Raises a clear error if required values are missing or invalid.
    """
    # Load YAML configuration
    yaml_config = _load_yaml_config()
    
    # Extract values from YAML structure
    ollama_config = yaml_config.get("ollama", {})
    llm_config = yaml_config.get("llm", {})
    embeddings_config = yaml_config.get("embeddings", {})
    limits_config = yaml_config.get("limits", {})
    scoring_config = yaml_config.get("scoring", {})
    rate_limiting_config = yaml_config.get("rate_limiting", {})
    
    # Get embed_model_name (required)
    embed_model_name: Optional[str] = embeddings_config.get("model_name")
    if not embed_model_name:
        raise RuntimeError(
            "embeddings.model_name is required in config.yaml but not set. "
            "Configure it to point to a valid SentenceTransformer model."
        )

    try:
        settings = Settings(
            # Ollama settings from YAML
            ollama_base_url=ollama_config.get("base_url", "http://localhost:11434"),
            ollama_default_model=ollama_config.get("default_model", "qwen3:1.7b"),
            
            # LLM provider settings from YAML
            llm_provider=llm_config.get("provider", "ollama"),
            groq_model=llm_config.get("groq_model", "llama-3.3-70b-versatile"),
            
            # Embeddings from YAML
            embed_model_name=embed_model_name,
            
            # Limits from YAML
            max_jd_chars=limits_config.get("max_jd_chars", 8000),
            max_resume_chars=limits_config.get("max_resume_chars", 20000),
            max_upload_bytes=limits_config.get("max_upload_bytes", 5 * 1024 * 1024),
            max_pdf_pages=limits_config.get("max_pdf_pages", 20),
            max_questions_per_category=limits_config.get("max_questions_per_category", 25),
            
            # Scoring weights from YAML
            mandatory_question_weight=scoring_config.get("mandatory_question_weight", 2.0),
            optional_question_weight=scoring_config.get("optional_question_weight", 1.0),
            mandatory_cap_weight=scoring_config.get("mandatory_cap_weight", 0.5),
            
            # Rate limiting from YAML
            max_requests_per_minute=rate_limiting_config.get("max_requests_per_minute", 30),
            
            # Secrets from environment variables only
            groq_api_key=os.getenv("GROQ_API_KEY"),
            api_key=os.getenv("API_KEY"),
        )
    except ValidationError as exc:
        raise RuntimeError(f"Invalid application settings: {exc}") from exc

    return settings
