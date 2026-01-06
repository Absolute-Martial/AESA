"""
AI memory and guideline tools for the AI agent.

These tools allow the AI agent to store and retrieve long-term memories
and user-defined guidelines for personalized assistance.

Requirements: 18.1, 18.2, 18.3, 18.5
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIMemory, AIGuideline
from app.tools.schedule_tools import get_tool_context

logger = logging.getLogger(__name__)


@tool
async def save_memory(key: str, value: str) -> dict[str, Any]:
    """
    Save information to AI long-term memory.

    Use this tool to remember user preferences, habits, or any
    information that should persist across conversations.

    Args:
        key: Memory key (e.g., "preferred_study_time", "favorite_subject")
        value: Information to remember

    Returns:
        Success status and saved memory details
    """
    user_id, db = get_tool_context()

    try:
        # Check if memory with this key already exists
        result = await db.execute(
            select(AIMemory).where(
                and_(
                    AIMemory.user_id == UUID(user_id),
                    AIMemory.key == key,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing memory
            existing.value = value
            existing.updated_at = datetime.utcnow()
            await db.flush()
            await db.refresh(existing)

            logger.info(f"Updated memory: {key}")

            return {
                "success": True,
                "action": "updated",
                "key": key,
                "value": value,
                "message": f"Updated memory '{key}'",
            }
        else:
            # Create new memory
            memory = AIMemory(
                user_id=UUID(user_id),
                key=key,
                value=value,
            )

            db.add(memory)
            await db.flush()
            await db.refresh(memory)

            logger.info(f"Saved new memory: {key}")

            return {
                "success": True,
                "action": "created",
                "key": key,
                "value": value,
                "message": f"Saved memory '{key}'",
            }

    except Exception as e:
        logger.error(f"Failed to save memory: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_memory(key: str) -> dict[str, Any]:
    """
    Retrieve information from AI memory.

    Use this tool to recall previously stored user preferences
    or information.

    Args:
        key: Memory key to retrieve

    Returns:
        Stored value or indication that key doesn't exist
    """
    user_id, db = get_tool_context()

    try:
        result = await db.execute(
            select(AIMemory).where(
                and_(
                    AIMemory.user_id == UUID(user_id),
                    AIMemory.key == key,
                )
            )
        )
        memory = result.scalar_one_or_none()

        if memory:
            return {
                "success": True,
                "found": True,
                "key": key,
                "value": memory.value,
                "updated_at": memory.updated_at.isoformat()
                if memory.updated_at
                else None,
            }
        else:
            return {
                "success": True,
                "found": False,
                "key": key,
                "value": None,
                "message": f"No memory found for key '{key}'",
            }

    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def forget_memory(key: str) -> dict[str, Any]:
    """
    Remove information from AI memory.

    Use this tool to delete outdated or incorrect information
    from the AI's long-term memory.

    Args:
        key: Memory key to forget

    Returns:
        Success status
    """
    user_id, db = get_tool_context()

    try:
        result = await db.execute(
            delete(AIMemory).where(
                and_(
                    AIMemory.user_id == UUID(user_id),
                    AIMemory.key == key,
                )
            )
        )

        if result.rowcount > 0:
            await db.flush()
            logger.info(f"Forgot memory: {key}")

            return {
                "success": True,
                "key": key,
                "message": f"Forgot memory '{key}'",
            }
        else:
            return {
                "success": True,
                "key": key,
                "message": f"No memory found for key '{key}'",
            }

    except Exception as e:
        logger.error(f"Failed to forget memory: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def add_guideline(guideline: str) -> dict[str, Any]:
    """
    Add a user-defined guideline for AI behavior.

    Use this tool to add rules or preferences that the AI should
    follow in future interactions.

    Args:
        guideline: The guideline text (e.g., "Always suggest breaks after 90 minutes of study")

    Returns:
        Success status and guideline details
    """
    user_id, db = get_tool_context()

    try:
        # Create new guideline
        ai_guideline = AIGuideline(
            user_id=UUID(user_id),
            guideline=guideline,
            is_active=True,
        )

        db.add(ai_guideline)
        await db.flush()
        await db.refresh(ai_guideline)

        logger.info(f"Added guideline: {guideline[:50]}...")

        return {
            "success": True,
            "id": str(ai_guideline.id),
            "guideline": guideline,
            "is_active": True,
            "message": "Guideline added successfully",
        }

    except Exception as e:
        logger.error(f"Failed to add guideline: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def list_guidelines() -> dict[str, Any]:
    """
    List all active guidelines for the user.

    Use this tool to see what guidelines are currently active
    for the AI's behavior.

    Returns:
        List of active guidelines
    """
    user_id, db = get_tool_context()

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

        return {
            "success": True,
            "count": len(guidelines),
            "guidelines": [
                {
                    "id": str(g.id),
                    "guideline": g.guideline,
                    "created_at": g.created_at.isoformat(),
                }
                for g in guidelines
            ],
        }

    except Exception as e:
        logger.error(f"Failed to list guidelines: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def deactivate_guideline(guideline_id: str) -> dict[str, Any]:
    """
    Deactivate a guideline.

    Use this tool to disable a guideline without deleting it.

    Args:
        guideline_id: ID of the guideline to deactivate

    Returns:
        Success status
    """
    user_id, db = get_tool_context()

    try:
        result = await db.execute(
            select(AIGuideline).where(
                and_(
                    AIGuideline.id == UUID(guideline_id),
                    AIGuideline.user_id == UUID(user_id),
                )
            )
        )
        guideline = result.scalar_one_or_none()

        if not guideline:
            return {
                "success": False,
                "error": f"Guideline {guideline_id} not found",
            }

        guideline.is_active = False
        await db.flush()

        logger.info(f"Deactivated guideline: {guideline_id}")

        return {
            "success": True,
            "id": guideline_id,
            "message": "Guideline deactivated",
        }

    except Exception as e:
        logger.error(f"Failed to deactivate guideline: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Helper functions for memory operations (used by prompt builder)


async def get_all_memories(db: AsyncSession, user_id: str) -> list[dict[str, Any]]:
    """
    Get all memories for a user.

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        List of memory dictionaries
    """
    result = await db.execute(select(AIMemory).where(AIMemory.user_id == UUID(user_id)))
    memories = list(result.scalars().all())

    return [
        {
            "key": m.key,
            "value": m.value,
        }
        for m in memories
    ]


async def get_active_guidelines(db: AsyncSession, user_id: str) -> list[str]:
    """
    Get all active guidelines for a user.

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        List of guideline strings
    """
    result = await db.execute(
        select(AIGuideline).where(
            and_(
                AIGuideline.user_id == UUID(user_id),
                AIGuideline.is_active,
            )
        )
    )
    guidelines = list(result.scalars().all())

    return [g.guideline for g in guidelines]


# Export all memory tools
MEMORY_TOOLS = [
    save_memory,
    get_memory,
    forget_memory,
    add_guideline,
    list_guidelines,
    deactivate_guideline,
]
