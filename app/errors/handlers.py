"""
Central error handlers that turn domain exceptions into clean JSON responses.
No raw upstream errors or secrets are ever leaked.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.callmissed_client import (
    CallMissedError,
    CallMissedAuthError,
    CallMissedPaymentError,
    CallMissedRateLimitError,
    CallMissedUnsupportedError,
    CallMissedUpstreamError,
)


async def callmissed_error_handler(request: Request, exc: CallMissedError) -> JSONResponse:
    headers = {}
    if isinstance(exc, CallMissedRateLimitError) and exc.retry_after is not None:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"message": exc.detail, "type": _error_type(exc)}},
        headers=headers,
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Catch-all — never leak details
    return JSONResponse(
        status_code=500,
        content={"error": {"message": "Internal server error.", "type": "internal_error"}},
    )


def _error_type(exc: CallMissedError) -> str:
    mapping = {
        CallMissedAuthError: "authentication_error",
        CallMissedPaymentError: "payment_required",
        CallMissedRateLimitError: "rate_limit_error",
        CallMissedUnsupportedError: "invalid_request_error",
        CallMissedUpstreamError: "upstream_error",
    }
    return mapping.get(type(exc), "api_error")