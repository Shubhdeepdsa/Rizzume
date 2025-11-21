import os
import requests
from typing import List, Dict, Any


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3:1.7b")


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

    NOTE:
    - stream=False: we assume non-streaming for now to keep it simple.
    - If you later want streaming, we can extend this.
    """
    used_model = model or OLLAMA_DEFAULT_MODEL

    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload: Dict[str, Any] = {
        "model": used_model,
        "stream": stream,
        "messages": messages,
    }

    payload.update(extra_kwargs)

    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    return data
