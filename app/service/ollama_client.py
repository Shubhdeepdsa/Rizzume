import logging
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from app.config import get_settings
from app.errors import LLMBackendError

load_dotenv()

logger = logging.getLogger(__name__)


def call_ollama_chat(
    messages: List[Dict[str, str]],
    model: str | None = None,
    stream: bool = False,
    **extra_kwargs: Any,
) -> Dict[str, Any]:
    """
    Thin wrapper over Ollama /api/chat.

    messages: list of dicts like:
      { "role": "system" | "user" | "assistant", "content": "..." }

    Returns the parsed JSON response from Ollama.

    NOTE: stream=False is assumed for now to keep things simple.
    """
    settings = get_settings()
    used_model = model or settings.ollama_default_model
    url = f"{settings.ollama_base_url}/api/chat"

    payload: Dict[str, Any] = {
        "model": used_model,
        "stream": stream,
        "messages": messages,
    }

    payload.update(extra_kwargs)

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.exception(
            "Error while calling Ollama at %s with model %s", url, used_model
        )
        raise LLMBackendError("Failed to call LLM backend.") from exc

    return data
