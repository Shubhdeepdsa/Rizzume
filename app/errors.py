from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException, status


class AppError(Exception):
    """Base class for application-level errors."""

    def __init__(self, message: str, *, code: str = "app_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ClientError(AppError):
    """Base class for 4xx-style client errors."""


class ServerError(AppError):
    """Base class for 5xx-style server errors."""


class AuthError(ClientError):
    """Authentication / authorization problem."""

    def __init__(self, message: str = "Unauthorized", code: str = "auth_error"):
        super().__init__(message, code=code)


class RateLimitError(ClientError):
    """Too many requests for the given client."""

    def __init__(self, message: str = "Too many requests", code: str = "rate_limited"):
        super().__init__(message, code=code)


class ValidationAppError(ClientError):
    """Semantic validation problem in the application layer."""

    def __init__(
        self, message: str = "Invalid request", code: str = "validation_error"
    ):
        super().__init__(message, code=code)


class LLMBackendError(ServerError):
    """Failure when calling or parsing the LLM backend."""

    def __init__(
        self,
        message: str = "LLM backend failure",
        code: str = "llm_backend_error",
    ):
        super().__init__(message, code=code)


def app_error_to_http(exc: AppError) -> HTTPException:
    """
    Map an AppError to a FastAPI HTTPException.

    We treat:
      - ClientError subclasses as 4xx.
      - ServerError subclasses as 5xx.
    """
    if isinstance(exc, AuthError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, RateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, ValidationAppError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ClientError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ServerError):
        status_code = status.HTTP_502_BAD_GATEWAY
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    detail: Dict[str, Any] = {
        "code": exc.code,
        "message": exc.message,
    }
    return HTTPException(status_code=status_code, detail=detail)

