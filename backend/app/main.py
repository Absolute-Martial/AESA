"""AESA Backend - FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.logging import setup_logging, log_system
from app.core.database import close_db, init_db
from app.api import (
    schedule_router,
    timeline_router,
    tasks_router,
    timer_router,
    goals_router,
    chat_router,
    register_error_handlers,
)
from app.core.database import async_session_maker
from app.graphql import create_graphql_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    setup_logging()
    log_system("info", "AESA Backend starting up")

    settings = get_settings()
    log_system("info", f"Debug mode: {settings.debug}")

    await init_db()

    yield

    # Shutdown
    log_system("info", "AESA Backend shutting down")
    await close_db()


async def _graphql_db_session_middleware(request, call_next) -> Response:
    if request.url.path != "/graphql":
        return await call_next(request)

    db = async_session_maker()
    request.state.db = db
    try:
        response = await call_next(request)
        return response
    finally:
        await db.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Engineering Study Assistant - Core Scheduling API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure GraphQL DB sessions are always closed
    app.add_middleware(BaseHTTPMiddleware, dispatch=_graphql_db_session_middleware)

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    # Include API routers
    app.include_router(schedule_router, prefix="/api")
    app.include_router(timeline_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(timer_router, prefix="/api")
    app.include_router(goals_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")

    # Include GraphQL router
    graphql_router = create_graphql_router()
    app.include_router(graphql_router, prefix="")

    @app.get("/health")
    async def health_check() -> dict:
        """
        Health check endpoint returning copilot-api status.

        Returns:
            Health status including copilot-api availability
        """
        settings = get_settings()
        copilot_status = "unknown"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.copilot_api_url}/health")
                copilot_status = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
        except Exception:
            copilot_status = "unavailable"

        return {
            "status": "healthy",
            "service": "aesa-backend",
            "version": "0.1.0",
            "copilot_api": copilot_status,
        }


# Create the application instance
app = create_app()
