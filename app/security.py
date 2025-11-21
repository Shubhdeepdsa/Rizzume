from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import Depends, Header, Request

from app.config import get_settings
from app.errors import AuthError, RateLimitError


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """
    If APP_API_KEY is set in configuration, requests must include:
      X-API-Key: <value>

    If APP_API_KEY is not set, auth is effectively disabled (useful in dev).
    """
    settings = get_settings()
    expected = getattr(settings, "api_key", None)
    if not expected:
        # Auth disabled (dev mode).
        return

    if x_api_key != expected:
        raise AuthError("Invalid API key.")


_WINDOW_SECONDS = 60.0
_DEFAULT_MAX_REQUESTS_PER_WINDOW = 30

_request_history: Dict[str, Deque[float]] = defaultdict(deque)


def _get_rate_limit_settings() -> tuple[int, float]:
    settings = get_settings()
    max_requests = getattr(settings, "max_requests_per_minute", None)
    if max_requests is None:
        max_requests = _DEFAULT_MAX_REQUESTS_PER_WINDOW
    return max_requests, _WINDOW_SECONDS


def rate_limiter(request: Request, _: None = Depends(require_api_key)) -> None:
    """
    Naive in-memory, per-client rate limiter.

    The key is derived from the API key if present, otherwise from client host.
    This is best-effort and suitable for a single-instance deployment or demo.
    """
    max_requests, window_seconds = _get_rate_limit_settings()
    now = time.time()

    client_key = request.headers.get("X-API-Key") or request.client.host or "anonymous"
    dq = _request_history[client_key]

    # Drop timestamps outside the current window.
    while dq and now - dq[0] > window_seconds:
        dq.popleft()

    if len(dq) >= max_requests:
        raise RateLimitError(
            f"Rate limit exceeded: max {max_requests} requests per {int(window_seconds)}s."
        )

    dq.append(now)

