"""
Unified LLM client that supports multiple providers (Ollama, Groq).

Usage:
    from app.service.llm_client import call_llm_chat
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]
    response = call_llm_chat(messages)
    # Returns: {"message": {"role": "assistant", "content": "..."}}
"""

import logging
import time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from app.config import get_settings
from app.errors import LLMBackendError

load_dotenv()

logger = logging.getLogger(__name__)

# Retry configuration for rate limits
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2.0  # seconds


def _call_ollama(
    messages: List[Dict[str, str]],
    model: str,
    base_url: str,
    **extra_kwargs: Any,
) -> Dict[str, Any]:
    """
    Call Ollama /api/chat endpoint.
    """
    url = f"{base_url}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "stream": False,
        "messages": messages,
    }
    payload.update(extra_kwargs)

    logger.info("📤 [Ollama] Calling model '%s' at %s", model, base_url)

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        logger.info("✅ [Ollama] Response received from model '%s'", model)
        return resp.json()
    except requests.RequestException as exc:
        logger.exception("❌ [Ollama] Error calling model %s at %s", model, url)
        raise LLMBackendError("Failed to call Ollama backend.") from exc


def _call_groq(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    **extra_kwargs: Any,
) -> Dict[str, Any]:
    """
    Call Groq API (OpenAI-compatible) with retry logic for rate limits.
    Returns response in Ollama-compatible format for consistency.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    payload.update(extra_kwargs)

    logger.info("📤 [Groq] Calling model '%s'", model)

    last_exception = None
    delay = INITIAL_RETRY_DELAY

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            
            # Handle rate limiting with retry
            if resp.status_code == 429:
                if attempt < MAX_RETRIES:
                    retry_after = resp.headers.get("retry-after")
                    wait_time = float(retry_after) if retry_after else delay
                    logger.warning(
                        "⚠️ [Groq] Rate limited (429). Retry %d/%d after %.1fs...",
                        attempt + 1, MAX_RETRIES, wait_time
                    )
                    time.sleep(wait_time)
                    delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error("❌ [Groq] Rate limit exceeded after %d retries", MAX_RETRIES)
                    resp.raise_for_status()
            
            resp.raise_for_status()
            data = resp.json()
            logger.info("✅ [Groq] Response received from model '%s'", model)
            break
            
        except requests.RequestException as exc:
            last_exception = exc
            if attempt < MAX_RETRIES and "429" in str(exc):
                logger.warning(
                    "⚠️ [Groq] Request failed with rate limit. Retry %d/%d after %.1fs...",
                    attempt + 1, MAX_RETRIES, delay
                )
                time.sleep(delay)
                delay *= 2
                continue
            logger.exception("❌ [Groq] Error calling model %s", model)
            raise LLMBackendError("Failed to call Groq backend.") from exc
    else:
        # If we exhausted all retries
        raise LLMBackendError("Failed to call Groq backend after retries.") from last_exception

    # Convert OpenAI-style response to Ollama-style for consistency
    # OpenAI format: {"choices": [{"message": {"role": "assistant", "content": "..."}}]}
    # Ollama format: {"message": {"role": "assistant", "content": "..."}}
    try:
        openai_message = data["choices"][0]["message"]
        return {
            "message": {
                "role": openai_message.get("role", "assistant"),
                "content": openai_message.get("content", ""),
            },
            "model": model,
        }
    except (KeyError, IndexError) as exc:
        logger.exception("❌ [Groq] Unexpected response format: %s", data)
        raise LLMBackendError("Invalid response format from Groq.") from exc


def call_llm_chat(
    messages: List[Dict[str, str]],
    model: str | None = None,
    **extra_kwargs: Any,
) -> Dict[str, Any]:
    """
    Unified LLM chat interface.
    
    Automatically routes to the configured provider (Ollama or Groq).
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        model: Optional model override. Uses provider's default if not specified.
        **extra_kwargs: Additional arguments passed to the provider.
    
    Returns:
        Dict with 'message' key containing the assistant response.
        Format: {"message": {"role": "assistant", "content": "..."}}
    
    Raises:
        LLMBackendError: If the LLM call fails.
        RuntimeError: If provider is not configured correctly.
    """
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        used_model = model or settings.ollama_default_model
        return _call_ollama(
            messages=messages,
            model=used_model,
            base_url=settings.ollama_base_url,
            **extra_kwargs,
        )
    elif provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is required when LLM_PROVIDER is set to 'groq'. "
                "Set it in your .env file or environment variables."
            )
        used_model = model or settings.groq_model
        return _call_groq(
            messages=messages,
            model=used_model,
            api_key=settings.groq_api_key,
            **extra_kwargs,
        )
    else:
        raise RuntimeError(
            f"Unknown LLM provider: '{provider}'. "
            "Supported providers: 'ollama', 'groq'."
        )
