from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple

from fastapi import Depends, Header, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings
from app.errors import AuthError, RateLimitError
from app.service.pocketbase import get_pocketbase_service, PocketBaseService

security = HTTPBearer()

async def get_current_user_token(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    return creds.credentials

async def get_current_user(
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service)
) -> Dict:
    """
    Validates token via PB and returns the User Record.
    Also acts as 'require_auth'.
    """
    try:
        # This calls /api/collections/users/auth-refresh
        # Return format: { token: "...", record: {...}, meta: {...} }
        start = time.time()
        res = await pb.auth_refresh(token)
        # We can optimize by decoding JWT locally if we had the secret,
        # but calling PB guarantees revocation checks.
        record = res.get("record")
        if not record:
             raise AuthError("Token valid but no record returned.")
        return record
    except Exception as e:
        # Map specific PB errors if needed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """
    Legacy API Key Check (Optional).
    """
    settings = get_settings()
    expected = getattr(settings, "api_key", None)
    if not expected:
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


def rate_limiter(request: Request) -> None:
    """
    Naive in-memory rate limiter.
    """
    # Skip for now or adapt to use User ID if available? 
    # For now keep naive host-based.
    max_requests, window_seconds = _get_rate_limit_settings()
    now = time.time()

    client_key = request.client.host or "anonymous"
    dq = _request_history[client_key]

    while dq and now - dq[0] > window_seconds:
        dq.popleft()

    if len(dq) >= max_requests:
        raise RateLimitError(
            f"Rate limit exceeded: max {max_requests} requests per {int(window_seconds)}s."
        )

    dq.append(now)
