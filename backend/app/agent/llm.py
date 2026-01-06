"""
LLM client configuration for copilot-api.

This module provides the LLM client that connects to copilot-api
for natural language processing capabilities.

Requirements: 6.2, 6.6
"""

import logging

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    """Raised when the LLM service is unavailable."""

    pass


def get_llm_client(
    temperature: float = 0.7,
    max_tokens: int = 2048,
    *,
    base_url: str | None = None,
    model: str | None = None,
) -> ChatOpenAI:
    """
    Get a configured LLM client for copilot-api.

    Args:
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response

    Returns:
        Configured ChatOpenAI client
    """
    settings = get_settings()

    resolved_base_url = base_url or f"{settings.copilot_api_url}/v1"
    resolved_model = model or "gpt-4"

    return ChatOpenAI(
        base_url=resolved_base_url,
        api_key="copilot-api",  # copilot-api doesn't require real key
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def check_llm_availability() -> bool:
    """
    Check if the LLM service (copilot-api) is available.

    Returns:
        True if available, False otherwise
    """
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.copilot_api_url}/health")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")
        return False


def get_fallback_message(user_message: str) -> str:
    """
    Provide a helpful fallback message when LLM is unavailable.

    Args:
        user_message: The user's original message

    Returns:
        Helpful fallback response
    """
    return (
        "I'm having trouble connecting to my AI backend right now. "
        "You can still use the schedule manually:\n\n"
        "• Click 'Add Task' to create new tasks\n"
        "• Drag tasks between columns to reschedule\n"
        "• Use the timer to track your study sessions\n"
        "• Check the Flow Board for your daily schedule\n\n"
        "I'll be back online soon!"
    )
