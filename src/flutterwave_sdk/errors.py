from __future__ import annotations

from typing import Any, Mapping, Optional


class FlutterwaveError(Exception):
    """Base exception for all SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        code: str | None = None,
        error_type: str | None = None,
        response: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.code = code
        self.error_type = error_type
        self.response = response
        self.headers = headers

    def __str__(self) -> str:
        detail = self.message
        if self.code:
            detail = f"{detail} (code={self.code})"
        if self.http_status:
            detail = f"{detail} [HTTP {self.http_status}]"
        return detail


class APIConnectionError(FlutterwaveError):
    """Raised when the SDK cannot connect to Flutterwave."""


class APIError(FlutterwaveError):
    """Raised for non-specific API errors."""


class BadRequestError(APIError):
    """Raised for HTTP 400 responses."""


class AuthenticationError(APIError):
    """Raised for HTTP 401 responses."""


class PermissionError(APIError):
    """Raised for HTTP 403 responses."""


class NotFoundError(APIError):
    """Raised for HTTP 404 responses."""


class ConflictError(APIError):
    """Raised for HTTP 409 responses, commonly idempotency conflicts."""


class RateLimitError(APIError):
    """Raised for HTTP 429 responses."""


class InvalidRequestOptionsError(FlutterwaveError):
    """Raised when SDK request options are invalid."""


def _extract_error(payload: Mapping[str, Any] | None) -> tuple[str, Optional[str], Optional[str]]:
    if not payload:
        return "Flutterwave API error", None, None

    error = payload.get("error")
    if isinstance(error, Mapping):
        message = str(error.get("message") or payload.get("message") or "Flutterwave API error")
        code = None if error.get("code") is None else str(error.get("code"))
        error_type = None if error.get("type") is None else str(error.get("type"))
        return message, code, error_type

    if payload.get("message"):
        return str(payload["message"]), None, None

    return "Flutterwave API error", None, None


def error_from_response(
    status_code: int,
    payload: Mapping[str, Any] | None,
    headers: Mapping[str, str] | None = None,
) -> FlutterwaveError:
    message, code, error_type = _extract_error(payload)
    kwargs = {
        "http_status": status_code,
        "code": code,
        "error_type": error_type,
        "response": payload,
        "headers": headers,
    }
    if status_code == 400:
        return BadRequestError(message, **kwargs)
    if status_code == 401:
        return AuthenticationError(message, **kwargs)
    if status_code == 403:
        return PermissionError(message, **kwargs)
    if status_code == 404:
        return NotFoundError(message, **kwargs)
    if status_code == 409:
        return ConflictError(message, **kwargs)
    if status_code == 429:
        return RateLimitError(message, **kwargs)
    return APIError(message, **kwargs)
