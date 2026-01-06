"""
Comprehensive logging system for AESA backend.

Implements:
- log_system function with levels: error, warning, info, debug
- Structured logging format suitable for analysis
- Context capture for errors (endpoint, params, stack trace)
- AI tool invocation logging
- copilot-api error logging

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.core.config import get_settings


class UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUID objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter for analysis.

    Outputs logs in a structured format with timestamp, level,
    message, and optional context as JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured output."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context if present
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, cls=UUIDEncoder)


def setup_logging() -> logging.Logger:
    """
    Set up the AESA logging system.

    Returns:
        Configured logger instance
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("aesa")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with structured format as it works
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    return logger


# Initialize logger on module load
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get the AESA logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def log_system(
    level: str,
    message: str,
    context: Optional[dict] = None,
) -> None:
    """
    Log a system message with optional context.

    This is the main logging function implementing Requirement 12.1.

    Args:
        level: Log level (error, warning, info, debug)
        message: Log message
        context: Optional context dictionary with additional information

    Example:
        log_system("info", "User logged in", {"user_id": "123"})
        log_system("error", "Database connection failed", {"host": "localhost"})
    """
    logger = get_logger()

    # Create log record with context
    extra = {"context": context} if context else {}

    level_map = {
        "error": logger.error,
        "warning": logger.warning,
        "info": logger.info,
        "debug": logger.debug,
    }

    log_func = level_map.get(level.lower(), logger.info)
    log_func(message, extra=extra)


def log_api_error(
    endpoint: str,
    method: str,
    params: Optional[dict] = None,
    error: Optional[Exception] = None,
    status_code: int = 500,
) -> None:
    """
    Log an API error with full context.

    Implements Requirement 12.2: Log errors with full context
    (endpoint, params, stack trace).

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        params: Request parameters
        error: Exception that occurred
        status_code: HTTP status code
    """
    context = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
    }

    if params:
        # Sanitize sensitive data
        sanitized_params = _sanitize_params(params)
        context["params"] = sanitized_params

    if error:
        context["error_type"] = type(error).__name__
        context["error_message"] = str(error)
        context["stack_trace"] = traceback.format_exc()

    log_system("error", f"API error: {method} {endpoint}", context)


def log_ai_tool_invocation(
    tool_name: str,
    parameters: dict,
    result: Any,
    duration_ms: Optional[float] = None,
    success: bool = True,
) -> None:
    """
    Log an AI tool invocation.

    Implements Requirement 12.3: Log AI tool name, parameters, and result.

    Args:
        tool_name: Name of the AI tool invoked
        parameters: Tool parameters
        result: Tool execution result
        duration_ms: Execution duration in milliseconds
        success: Whether the tool executed successfully
    """
    context = {
        "tool_name": tool_name,
        "parameters": _sanitize_params(parameters),
        "success": success,
    }

    if duration_ms is not None:
        context["duration_ms"] = round(duration_ms, 2)

    # Truncate result if too large
    result_str = str(result)
    if len(result_str) > 1000:
        result_str = result_str[:1000] + "... [truncated]"
    context["result"] = result_str

    level = "info" if success else "error"
    log_system(level, f"AI tool invoked: {tool_name}", context)


def log_copilot_api_error(
    error: Exception,
    request_data: Optional[dict] = None,
    response_data: Optional[dict] = None,
) -> None:
    """
    Log a copilot-api error.

    Implements Requirement 12.5: Log copilot-api errors with response details.

    Args:
        error: Exception that occurred
        request_data: Request data sent to copilot-api
        response_data: Response data received (if any)
    """
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "stack_trace": traceback.format_exc(),
    }

    if request_data:
        # Sanitize and truncate request data
        sanitized = _sanitize_params(request_data)
        context["request"] = _truncate_dict(sanitized, max_length=500)

    if response_data:
        context["response"] = _truncate_dict(response_data, max_length=500)

    log_system("error", "copilot-api error", context)


def log_database_operation(
    operation: str,
    table: str,
    record_id: Optional[str] = None,
    success: bool = True,
    error: Optional[Exception] = None,
) -> None:
    """
    Log a database operation.

    Args:
        operation: Operation type (INSERT, UPDATE, DELETE, SELECT)
        table: Table name
        record_id: Record ID if applicable
        success: Whether operation succeeded
        error: Exception if operation failed
    """
    context = {
        "operation": operation,
        "table": table,
        "success": success,
    }

    if record_id:
        context["record_id"] = record_id

    if error:
        context["error_type"] = type(error).__name__
        context["error_message"] = str(error)

    level = "debug" if success else "error"
    log_system(level, f"Database {operation} on {table}", context)


def _sanitize_params(params: dict) -> dict:
    """
    Sanitize parameters by removing sensitive data.

    Args:
        params: Parameters dictionary

    Returns:
        Sanitized parameters
    """
    sensitive_keys = {
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "auth",
        "credential",
        "private_key",
        "access_token",
    }

    sanitized = {}
    for key, value in params.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_params(value)
        else:
            sanitized[key] = value

    return sanitized


def _truncate_dict(data: dict, max_length: int = 500) -> dict:
    """
    Truncate dictionary values that are too long.

    Args:
        data: Dictionary to truncate
        max_length: Maximum length for string values

    Returns:
        Truncated dictionary
    """
    truncated = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > max_length:
            truncated[key] = value[:max_length] + "... [truncated]"
        elif isinstance(value, dict):
            truncated[key] = _truncate_dict(value, max_length)
        else:
            truncated[key] = value

    return truncated


# Convenience functions for common log levels
def log_error(message: str, context: Optional[dict] = None) -> None:
    """Log an error message."""
    log_system("error", message, context)


def log_warning(message: str, context: Optional[dict] = None) -> None:
    """Log a warning message."""
    log_system("warning", message, context)


def log_info(message: str, context: Optional[dict] = None) -> None:
    """Log an info message."""
    log_system("info", message, context)


def log_debug(message: str, context: Optional[dict] = None) -> None:
    """Log a debug message."""
    log_system("debug", message, context)
