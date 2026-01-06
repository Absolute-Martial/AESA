"""
Error handling middleware and utilities.

Implements:
- Standardized error response format
- Error code mapping
- Graceful degradation for C engine failures

Requirements: 5.4, 19.1, 19.2, 19.3, 19.4
"""

from enum import Enum
from typing import Optional, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import log_system
from app.scheduler.bridge import SchedulerError, SchedulerErrorCode


class ErrorCode(str, Enum):
    """Standard error codes for the API."""

    # Schedule errors (E001-E005)
    SCHEDULE_CONFLICT = "E001"
    NO_VALID_PLACEMENT = "E002"
    DEADLINE_IMPOSSIBLE = "E003"
    FIXED_SLOT_VIOLATION = "E004"
    ENGINE_TIMEOUT = "E005"

    # Service errors (E006-E010)
    LLM_UNAVAILABLE = "E006"
    INVALID_TASK_TYPE = "E007"
    DATABASE_ERROR = "E008"
    VALIDATION_ERROR = "E009"
    AUTHENTICATION_ERROR = "E010"

    # Resource errors (E011-E015)
    NOT_FOUND = "E011"
    ALREADY_EXISTS = "E012"
    PERMISSION_DENIED = "E013"
    RATE_LIMITED = "E014"
    SERVICE_UNAVAILABLE = "E015"

    # Generic errors
    INTERNAL_ERROR = "E500"
    BAD_REQUEST = "E400"


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    suggestion: Optional[str] = None
    context: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    success: bool = False
    error: ErrorDetail


# Error code to HTTP status mapping
ERROR_STATUS_MAP = {
    ErrorCode.SCHEDULE_CONFLICT: 409,
    ErrorCode.NO_VALID_PLACEMENT: 422,
    ErrorCode.DEADLINE_IMPOSSIBLE: 422,
    ErrorCode.FIXED_SLOT_VIOLATION: 400,
    ErrorCode.ENGINE_TIMEOUT: 504,
    ErrorCode.LLM_UNAVAILABLE: 503,
    ErrorCode.INVALID_TASK_TYPE: 400,
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.AUTHENTICATION_ERROR: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.ALREADY_EXISTS: 409,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.BAD_REQUEST: 400,
}


# Scheduler error code mapping
SCHEDULER_ERROR_MAP = {
    SchedulerErrorCode.NO_SOLUTION: ErrorCode.NO_VALID_PLACEMENT,
    SchedulerErrorCode.TIMEOUT: ErrorCode.ENGINE_TIMEOUT,
    SchedulerErrorCode.MEMORY: ErrorCode.ENGINE_TIMEOUT,
    SchedulerErrorCode.PARSE_ERROR: ErrorCode.INTERNAL_ERROR,
    SchedulerErrorCode.ENGINE_NOT_FOUND: ErrorCode.SERVICE_UNAVAILABLE,
    SchedulerErrorCode.UNKNOWN: ErrorCode.INTERNAL_ERROR,
}


# Default suggestions for error codes
ERROR_SUGGESTIONS = {
    ErrorCode.SCHEDULE_CONFLICT: "Try moving one of the conflicting tasks to a different time.",
    ErrorCode.NO_VALID_PLACEMENT: "Try removing some tasks or extending deadlines.",
    ErrorCode.DEADLINE_IMPOSSIBLE: "The deadline is too soon. Consider extending it or reducing task duration.",
    ErrorCode.FIXED_SLOT_VIOLATION: "Fixed time slots (classes, sleep) cannot be modified.",
    ErrorCode.ENGINE_TIMEOUT: "The optimization took too long. Try reducing the number of tasks.",
    ErrorCode.LLM_UNAVAILABLE: "AI assistant is temporarily unavailable. You can still use manual scheduling.",
    ErrorCode.INVALID_TASK_TYPE: "Please use a valid task type.",
    ErrorCode.DATABASE_ERROR: "A database error occurred. Please try again.",
    ErrorCode.NOT_FOUND: "The requested resource was not found.",
    ErrorCode.ALREADY_EXISTS: "A resource with this identifier already exists.",
}


class APIError(Exception):
    """Custom API error with structured response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[dict] = None,
        status_code: Optional[int] = None,
    ):
        self.code = code
        self.message = message
        self.suggestion = suggestion or ERROR_SUGGESTIONS.get(code)
        self.context = context or {}
        self.status_code = status_code or ERROR_STATUS_MAP.get(code, 500)
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Convert to ErrorResponse."""
        return ErrorResponse(
            success=False,
            error=ErrorDetail(
                code=self.code.value,
                message=self.message,
                suggestion=self.suggestion,
                context=self.context,
            ),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.to_response().model_dump()


def create_error_response(
    code: ErrorCode,
    message: str,
    suggestion: Optional[str] = None,
    context: Optional[dict] = None,
) -> dict:
    """
    Create a standardized error response dictionary.

    Property 11: Error Response Well-Formedness
    - Always contains valid error code
    - Always contains human-readable message
    - Optionally contains suggestion
    - Never empty or malformed
    """
    return {
        "success": False,
        "error": {
            "code": code.value,
            "message": message,
            "suggestion": suggestion or ERROR_SUGGESTIONS.get(code),
            "context": context or {},
        },
    }


def handle_scheduler_error(error: SchedulerError) -> dict:
    """
    Convert SchedulerError to standardized error response.

    Provides graceful degradation for C engine failures.
    """
    api_code = SCHEDULER_ERROR_MAP.get(error.code, ErrorCode.INTERNAL_ERROR)

    return create_error_response(
        code=api_code,
        message=error.message,
        suggestion=error.suggestion,
        context=error.context,
    )


def handle_llm_fallback(user_message: str) -> str:
    """
    Provide helpful response when LLM is unavailable.

    Graceful degradation for AI assistant failures.
    """
    return (
        "I'm having trouble connecting to my AI backend right now. "
        "You can still use the schedule manually:\n"
        "• Click 'Add Task' to create new tasks\n"
        "• Drag tasks between columns to reschedule\n"
        "• Use the timer to track your study sessions\n\n"
        "I'll be back online soon!"
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """FastAPI exception handler for APIError."""
    log_system(
        "error",
        f"API Error: {exc.code.value} - {exc.message}",
        context={
            "path": str(request.url.path),
            "method": request.method,
            "code": exc.code.value,
            "context": exc.context,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def scheduler_error_handler(
    request: Request, exc: SchedulerError
) -> JSONResponse:
    """FastAPI exception handler for SchedulerError."""
    log_system(
        "error",
        f"Scheduler Error: {exc.code.value} - {exc.message}",
        context={
            "path": str(request.url.path),
            "method": request.method,
            "code": exc.code.value,
            "context": exc.context,
        },
    )

    response = handle_scheduler_error(exc)
    status_code = ERROR_STATUS_MAP.get(
        SCHEDULER_ERROR_MAP.get(exc.code, ErrorCode.INTERNAL_ERROR),
        500,
    )

    return JSONResponse(
        status_code=status_code,
        content=response,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """FastAPI exception handler for HTTPException."""
    # Map HTTP status to error code
    status_to_code = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.ALREADY_EXISTS,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code=code,
            message=str(exc.detail),
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler for unhandled exceptions."""
    log_system(
        "error",
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        context={
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            suggestion="Please try again. If the problem persists, contact support.",
        ),
    )


def register_error_handlers(app: Any) -> None:
    """Register all error handlers with the FastAPI app."""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(SchedulerError, scheduler_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
