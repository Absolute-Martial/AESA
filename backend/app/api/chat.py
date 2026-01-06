"""
Chat API endpoint for AI agent interaction.

This module provides the POST /api/chat endpoint for processing
user messages through the LangGraph AI agent.

Requirements: 6.3, 6.4
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import log_system
from app.agent import (
    AESAAgent,
    AgentContext,
    check_llm_availability,
    get_fallback_message,
)
from sqlalchemy import select
from app.models import AssistantSettings

from app.agent.prompt_builder import build_system_prompt
from app.tools import ALL_TOOLS, set_tool_context
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    user_id: str = Field(..., description="User UUID")
    context: Optional[dict[str, Any]] = Field(
        default=None, description="Optional context"
    )


class ToolCallInfo(BaseModel):
    """Information about a tool call made by the agent."""

    name: str
    arguments: dict[str, Any]


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    content: str = Field(..., description="AI response content")
    tool_calls: list[ToolCallInfo] = Field(
        default_factory=list, description="Tools invoked"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Default user ID for development (single-user mode)
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Send a message to the AI agent and receive a response.

    The agent will process the message, potentially invoke tools,
    and return a response with any actions taken.

    Args:
        request: Chat request with message and user context
        db: Database session

    Returns:
        ChatResponse with AI response and tool call information
    """
    log_system(
        "info",
        f"Chat message received from user {request.user_id}",
        {"message_length": len(request.message)},
    )

    try:
        # Check LLM availability first
        is_available = await check_llm_availability()
        if not is_available:
            log_system("warning", "LLM service unavailable, returning fallback")
            return ChatResponse(
                content=get_fallback_message(request.message),
                tool_calls=[],
                error="LLM service unavailable",
            )

        # Set tool context for database operations
        set_tool_context(request.user_id, db)

        # Build agent context
        context = None
        if request.context:
            context = AgentContext(
                current_task_id=request.context.get("current_task_id"),
                current_task_title=request.context.get("current_task_title"),
                active_subject=request.context.get("active_subject"),
                preferences=request.context.get("preferences", {}),
            )

        # Build system prompt with user memories and guidelines
        system_prompt = await build_system_prompt(db, request.user_id, context)

        # Load per-user assistant settings (if present)
        assistant_settings = None
        try:
            import uuid

            settings_result = await db.execute(
                select(AssistantSettings).where(
                    AssistantSettings.user_id == uuid.UUID(request.user_id)
                )
            )
            assistant_settings = settings_result.scalar_one_or_none()
        except Exception:
            assistant_settings = None

        # Create agent with all tools
        agent = AESAAgent(
            tools=ALL_TOOLS,
            llm_base_url=getattr(assistant_settings, "base_url", None),
            llm_model=getattr(assistant_settings, "model", None),
        )

        # Build message history with system prompt
        history = [SystemMessage(content=system_prompt)]

        # Process the message
        result = await agent.process_message(
            message=request.message,
            user_id=request.user_id,
            context=context,
            history=history,
        )

        # Extract tool call information
        tool_calls = []
        for tc in result.get("tool_calls", []):
            if isinstance(tc, dict):
                tool_calls.append(
                    ToolCallInfo(
                        name=tc.get("name", "unknown"),
                        arguments=tc.get("args", {}),
                    )
                )

        # Log the interaction
        log_system(
            "info",
            f"Chat response generated for user {request.user_id}",
            {
                "response_length": len(result.get("content", "")),
                "tool_calls": len(tool_calls),
            },
        )

        # Commit any database changes from tool calls
        await db.commit()

        return ChatResponse(
            content=result.get("content", ""),
            tool_calls=tool_calls,
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        log_system(
            "error", f"Chat processing failed: {e}", {"user_id": request.user_id}
        )

        # Rollback any partial changes
        await db.rollback()

        return ChatResponse(
            content=get_fallback_message(request.message),
            tool_calls=[],
            error=str(e),
        )


@router.get("/chat/status")
async def get_chat_status() -> dict[str, Any]:
    """
    Get the status of the chat service.

    Returns:
        Status information including LLM availability
    """
    is_available = await check_llm_availability()

    return {
        "status": "available" if is_available else "degraded",
        "llm_available": is_available,
        "tools_count": len(ALL_TOOLS),
        "tools": [t.name for t in ALL_TOOLS],
    }


# Create router for export
chat_router = router
