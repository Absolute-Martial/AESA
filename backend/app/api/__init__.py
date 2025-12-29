"""API routers and endpoints for AESA backend."""

from app.api.schedule import router as schedule_router
from app.api.timeline import router as timeline_router
from app.api.tasks import router as tasks_router
from app.api.timer import router as timer_router
from app.api.goals import router as goals_router
from app.api.chat import chat_router
from app.api.errors import (
    APIError,
    ErrorCode,
    ErrorResponse,
    ErrorDetail,
    create_error_response,
    register_error_handlers,
)

__all__ = [
    # Routers
    "schedule_router",
    "timeline_router",
    "tasks_router",
    "timer_router",
    "goals_router",
    "chat_router",
    # Error handling
    "APIError",
    "ErrorCode",
    "ErrorResponse",
    "ErrorDetail",
    "create_error_response",
    "register_error_handlers",
]
