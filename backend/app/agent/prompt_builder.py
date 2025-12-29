"""
Dynamic system prompt builder for the AI agent.

This module builds context-aware system prompts that include
user memories and guidelines for personalized assistance.

Requirements: 6.5, 18.4
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIMemory, AIGuideline
from app.agent.state import AgentContext

logger = logging.getLogger(__name__)


# Base system prompt template
BASE_SYSTEM_PROMPT = """You are AESA (AI Engineering Study Assistant), a helpful AI assistant for KU Engineering students.

Your role is to help students manage their study schedules, track progress, and optimize their learning.

## Your Capabilities

You can help with:
- Creating, moving, and deleting schedule blocks
- Finding optimal study times and deep work slots
- Planning backward from deadlines
- Scheduling spaced repetition for chapter revisions
- Preparing for exams and tests
- Tracking study goals and progress
- Remembering user preferences

## Important Guidelines

1. **Never hallucinate schedule information** - Always use tools to query actual data
2. **Be proactive** - Suggest optimizations and improvements
3. **Respect fixed blocks** - University classes and sleep cannot be moved
4. **Consider energy levels** - Schedule demanding tasks during peak energy times
5. **Encourage breaks** - Suggest breaks after 90 minutes of focused work

## Current Context

Today's date: {today_date}
"""


MEMORIES_SECTION = """
## User Memories

The following information has been saved about this user:

{memories}
"""


GUIDELINES_SECTION = """
## User Guidelines

The user has set the following guidelines for your behavior:

{guidelines}
"""


CONTEXT_SECTION = """
## Current Session Context

{context_info}
"""


async def get_user_memories(db: AsyncSession, user_id: str) -> list[dict[str, str]]:
    """
    Get all memories for a user.

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        List of memory dictionaries with key and value
    """
    try:
        result = await db.execute(
            select(AIMemory).where(AIMemory.user_id == UUID(user_id))
        )
        memories = list(result.scalars().all())

        return [{"key": m.key, "value": m.value} for m in memories]
    except Exception as e:
        logger.error(f"Failed to get user memories: {e}")
        return []


async def get_active_guidelines(db: AsyncSession, user_id: str) -> list[str]:
    """
    Get all active guidelines for a user.

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        List of guideline strings
    """
    try:
        result = await db.execute(
            select(AIGuideline)
            .where(
                and_(
                    AIGuideline.user_id == UUID(user_id),
                    AIGuideline.is_active,
                )
            )
            .order_by(AIGuideline.created_at.desc())
        )
        guidelines = list(result.scalars().all())

        return [g.guideline for g in guidelines]
    except Exception as e:
        logger.error(f"Failed to get active guidelines: {e}")
        return []


def format_memories(memories: list[dict[str, str]]) -> str:
    """
    Format memories for inclusion in the prompt.

    Args:
        memories: List of memory dictionaries

    Returns:
        Formatted string of memories
    """
    if not memories:
        return "No memories stored yet."

    lines = []
    for memory in memories:
        lines.append(f"- **{memory['key']}**: {memory['value']}")

    return "\n".join(lines)


def format_guidelines(guidelines: list[str]) -> str:
    """
    Format guidelines for inclusion in the prompt.

    Args:
        guidelines: List of guideline strings

    Returns:
        Formatted string of guidelines
    """
    if not guidelines:
        return "No custom guidelines set."

    lines = []
    for i, guideline in enumerate(guidelines, 1):
        lines.append(f"{i}. {guideline}")

    return "\n".join(lines)


def format_context(context: AgentContext) -> str:
    """
    Format current context for inclusion in the prompt.

    Args:
        context: Agent context object

    Returns:
        Formatted context string
    """
    lines = []

    if context.current_task_title:
        lines.append(f"- Current task: {context.current_task_title}")

    if context.active_subject:
        lines.append(f"- Active subject: {context.active_subject}")

    if context.preferences:
        pref_items = []
        for key, value in context.preferences.items():
            pref_items.append(f"  - {key}: {value}")
        if pref_items:
            lines.append("- User preferences:")
            lines.extend(pref_items)

    if not lines:
        return "No specific context for this session."

    return "\n".join(lines)


async def build_system_prompt(
    db: AsyncSession,
    user_id: str,
    context: Optional[AgentContext] = None,
) -> str:
    """
    Build a dynamic system prompt including user memories and guidelines.

    This function constructs a personalized system prompt that includes:
    - Base instructions for the AI
    - User's stored memories
    - User's active guidelines
    - Current session context

    Args:
        db: Database session
        user_id: User UUID string
        context: Optional agent context

    Returns:
        Complete system prompt string
    """
    # Get today's date
    today_date = datetime.now().strftime("%A, %B %d, %Y")

    # Start with base prompt
    prompt_parts = [BASE_SYSTEM_PROMPT.format(today_date=today_date)]

    # Add memories section
    memories = await get_user_memories(db, user_id)
    if memories:
        formatted_memories = format_memories(memories)
        prompt_parts.append(MEMORIES_SECTION.format(memories=formatted_memories))

    # Add guidelines section
    guidelines = await get_active_guidelines(db, user_id)
    if guidelines:
        formatted_guidelines = format_guidelines(guidelines)
        prompt_parts.append(GUIDELINES_SECTION.format(guidelines=formatted_guidelines))

    # Add context section
    if context:
        formatted_context = format_context(context)
        prompt_parts.append(CONTEXT_SECTION.format(context_info=formatted_context))

    return "\n".join(prompt_parts)


def build_system_prompt_sync(
    memories: list[dict[str, str]],
    guidelines: list[str],
    context: Optional[AgentContext] = None,
) -> str:
    """
    Build a system prompt synchronously (for testing).

    Args:
        memories: List of memory dictionaries
        guidelines: List of guideline strings
        context: Optional agent context

    Returns:
        Complete system prompt string
    """
    # Get today's date
    today_date = datetime.now().strftime("%A, %B %d, %Y")

    # Start with base prompt
    prompt_parts = [BASE_SYSTEM_PROMPT.format(today_date=today_date)]

    # Add memories section
    if memories:
        formatted_memories = format_memories(memories)
        prompt_parts.append(MEMORIES_SECTION.format(memories=formatted_memories))

    # Add guidelines section
    if guidelines:
        formatted_guidelines = format_guidelines(guidelines)
        prompt_parts.append(GUIDELINES_SECTION.format(guidelines=formatted_guidelines))

    # Add context section
    if context:
        formatted_context = format_context(context)
        prompt_parts.append(CONTEXT_SECTION.format(context_info=formatted_context))

    return "\n".join(prompt_parts)


def check_prompt_includes_memories(prompt: str, memories: list[dict[str, str]]) -> bool:
    """
    Check if a prompt includes all provided memories.

    Args:
        prompt: The system prompt
        memories: List of memory dictionaries

    Returns:
        True if all memories are included
    """
    for memory in memories:
        if memory["key"] not in prompt or memory["value"] not in prompt:
            return False
    return True


def check_prompt_includes_guidelines(prompt: str, guidelines: list[str]) -> bool:
    """
    Check if a prompt includes all provided guidelines.

    Args:
        prompt: The system prompt
        guidelines: List of guideline strings

    Returns:
        True if all guidelines are included
    """
    for guideline in guidelines:
        if guideline not in prompt:
            return False
    return True
