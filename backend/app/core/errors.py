"""Application error type and the handlers that render it.

API_SPEC.md section 8 requires every response - success or failure - to use the
`{data, error, request_id}` envelope. These handlers are the only place that
builds an error body, so that contract holds even for unhandled failures.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.context import request_id_var

logger = logging.getLogger(__name__)


class AppError(Exception):
    """An error carrying a canonical API_SPEC.md code and its HTTP status."""

    def __init__(self, code: str, message: str, http_status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


def _error_envelope(code: str, message: str) -> dict[str, Any]:
    return {
        "data": None,
        "error": {"code": code, "message": message},
        "request_id": request_id_var.get(),
    }


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "app_error",
        extra={"extra_fields": {"error_code": exc.code, "http_status": exc.http_status}},
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=_error_envelope(exc.code, exc.message),
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_envelope("INTERNAL_ERROR", "An unexpected error occurred."),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
