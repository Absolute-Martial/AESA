"""
Schedule management tools for the AI agent.

These tools allow the AI agent to create, move, and delete schedule blocks,
as well as retrieve optimized schedules.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.time_block import TimeBlock
from app.models.task import Task
from app.scheduler.service import SchedulerService
from app.scheduler.bridge import TaskInput

logger = logging.getLogger(__name__)


# Global user_id for tool context (set by the agent before tool execution)
_current_user_id: Optional[str] = None
_current_db_session: Optional[AsyncSession] = None


def set_tool_context(user_id: str, db: AsyncSession) -> None:
    """Set the current user context for tools."""
    global _current_user_id, _current_db_session
    _current_user_id = user_id
    _current_db_session = db


def get_tool_context() -> tuple[str, AsyncSession]:
    """Get the current tool context."""
    if _current_user_id is None or _current_db_session is None:
        raise RuntimeError("Tool context not set. Call set_tool_context first.")
    return _current_user_id, _current_db_session


@tool
async def create_time_block(
    title: str,
    block_type: str,
    start_time: str,
    duration_minutes: int,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a new time block in the schedule.

    Use this tool to add study sessions, revision blocks, assignments,
    or any other scheduled activity to the user's calendar.

    Args:
        title: Name of the time block (e.g., "Study Neural Networks")
        block_type: Type of block - one of: study, revision, practice,
                   assignment, lab_work, deep_work, break, free_time
        start_time: Start time in ISO format (e.g., "2025-12-29T09:00:00")
        duration_minutes: Duration in minutes (e.g., 60 for 1 hour)
        task_id: Optional ID of a linked task

    Returns:
        Created time block details including ID and times
    """
    user_id, db = get_tool_context()

    try:
        # Parse start time
        start_dt = datetime.fromisoformat(start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Create the time block
        time_block = TimeBlock(
            user_id=UUID(user_id),
            title=title,
            block_type=block_type,
            start_time=start_dt,
            end_time=end_dt,
            is_fixed=False,
            task_id=UUID(task_id) if task_id else None,
        )

        db.add(time_block)
        await db.flush()
        await db.refresh(time_block)

        logger.info(f"Created time block: {title} at {start_time}")

        return {
            "success": True,
            "id": str(time_block.id),
            "title": time_block.title,
            "block_type": time_block.block_type,
            "start_time": time_block.start_time.isoformat(),
            "end_time": time_block.end_time.isoformat(),
            "duration_minutes": duration_minutes,
        }

    except Exception as e:
        logger.error(f"Failed to create time block: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def move_time_block(
    block_id: str,
    new_start_time: str,
) -> dict[str, Any]:
    """
    Move an existing time block to a new time.

    Use this tool to reschedule an existing block to a different time
    while preserving its duration and other properties.

    Args:
        block_id: ID of the time block to move
        new_start_time: New start time in ISO format (e.g., "2025-12-29T14:00:00")

    Returns:
        Updated time block details
    """
    user_id, db = get_tool_context()

    try:
        # Find the time block
        result = await db.execute(
            select(TimeBlock).where(
                TimeBlock.id == UUID(block_id),
                TimeBlock.user_id == UUID(user_id),
            )
        )
        time_block = result.scalar_one_or_none()

        if not time_block:
            return {
                "success": False,
                "error": f"Time block {block_id} not found",
            }

        if time_block.is_fixed:
            return {
                "success": False,
                "error": "Cannot move a fixed time block (e.g., university class)",
            }

        # Calculate new times
        old_duration = time_block.end_time - time_block.start_time
        new_start_dt = datetime.fromisoformat(new_start_time)
        new_end_dt = new_start_dt + old_duration

        # Update the block
        time_block.start_time = new_start_dt
        time_block.end_time = new_end_dt

        await db.flush()
        await db.refresh(time_block)

        logger.info(f"Moved time block {block_id} to {new_start_time}")

        return {
            "success": True,
            "id": str(time_block.id),
            "title": time_block.title,
            "start_time": time_block.start_time.isoformat(),
            "end_time": time_block.end_time.isoformat(),
            "duration_minutes": int(old_duration.total_seconds() / 60),
        }

    except Exception as e:
        logger.error(f"Failed to move time block: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def delete_time_block(block_id: str) -> dict[str, Any]:
    """
    Delete a time block from the schedule.

    Use this tool to remove a scheduled block. Note that fixed blocks
    (like university classes) cannot be deleted.

    Args:
        block_id: ID of the time block to delete

    Returns:
        Success status
    """
    user_id, db = get_tool_context()

    try:
        # Find the time block first to check if it's fixed
        result = await db.execute(
            select(TimeBlock).where(
                TimeBlock.id == UUID(block_id),
                TimeBlock.user_id == UUID(user_id),
            )
        )
        time_block = result.scalar_one_or_none()

        if not time_block:
            return {
                "success": False,
                "error": f"Time block {block_id} not found",
            }

        if time_block.is_fixed:
            return {
                "success": False,
                "error": "Cannot delete a fixed time block (e.g., university class)",
            }

        title = time_block.title

        # Delete the block
        await db.delete(time_block)
        await db.flush()

        logger.info(f"Deleted time block {block_id}: {title}")

        return {
            "success": True,
            "message": f"Deleted time block: {title}",
        }

    except Exception as e:
        logger.error(f"Failed to delete time block: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_optimized_schedule(target_date: str) -> dict[str, Any]:
    """
    Get the AI-optimized schedule for a specific date.

    This tool retrieves the complete schedule for a day including
    all blocks, gaps, and suggestions for optimal task placement.

    Args:
        target_date: Date in YYYY-MM-DD format (e.g., "2025-12-29")

    Returns:
        Optimized day schedule with blocks, gaps, and stats
    """
    user_id, db = get_tool_context()

    try:
        # Parse the date
        date = datetime.strptime(target_date, "%Y-%m-%d")

        # Get the schedule using the scheduler service
        service = SchedulerService(db)
        schedule = await service.get_day_schedule(UUID(user_id), date)

        return {
            "success": True,
            "date": target_date,
            "schedule": schedule.to_dict(),
        }

    except Exception as e:
        logger.error(f"Failed to get optimized schedule: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_weekly_timeline(start_date: str) -> dict[str, Any]:
    """
    Get the weekly schedule starting from a specific date.

    This tool retrieves the complete schedule for 7 days including
    all blocks, gaps, and deep work opportunities.

    Args:
        start_date: Start date in YYYY-MM-DD format (e.g., "2025-12-29")

    Returns:
        Weekly schedule with daily breakdowns
    """
    user_id, db = get_tool_context()

    try:
        # Parse the date
        date = datetime.strptime(start_date, "%Y-%m-%d")

        # Get the week schedule
        service = SchedulerService(db)
        schedules = await service.get_week_schedule(UUID(user_id), date)

        return {
            "success": True,
            "start_date": start_date,
            "days": [s.to_dict() for s in schedules],
            "summary": {
                "total_study_minutes": sum(s.total_study_minutes for s in schedules),
                "total_deep_work_minutes": sum(s.deep_work_minutes for s in schedules),
                "days_with_deep_work": sum(
                    1 for s in schedules if s.has_deep_work_opportunity
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get weekly timeline: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def reschedule_all(
    start_date: str,
    num_days: int = 7,
) -> dict[str, Any]:
    """
    Reschedule all pending tasks using the optimization engine.

    This tool triggers a complete re-optimization of the schedule,
    placing all pending tasks into optimal time slots based on
    priorities, deadlines, and energy levels.

    Args:
        start_date: Start date for optimization in YYYY-MM-DD format
        num_days: Number of days to optimize (default: 7)

    Returns:
        Optimization result with new schedule
    """
    user_id, db = get_tool_context()

    try:
        # Parse the date
        date = datetime.strptime(start_date, "%Y-%m-%d")

        # Get all pending tasks
        result = await db.execute(
            select(Task)
            .where(
                Task.user_id == UUID(user_id),
                ~Task.is_completed,
            )
            .order_by(Task.priority.desc())
        )
        tasks = list(result.scalars().all())

        if not tasks:
            return {
                "success": True,
                "message": "No pending tasks to schedule",
                "tasks_scheduled": 0,
            }

        # Convert to TaskInput for the C engine
        task_inputs = []
        for i, task in enumerate(tasks):
            # Calculate deadline slot if deadline exists
            deadline_slot = -1
            if task.deadline:
                days_until = (task.deadline.date() - date.date()).days
                if days_until >= 0 and days_until < num_days:
                    # Convert to slot index (48 slots per day)
                    deadline_slot = days_until * 48 + 47  # End of deadline day

            task_inputs.append(
                TaskInput(
                    id=i,
                    name=task.title,
                    type=task.task_type,
                    duration_slots=task.duration_minutes // 30,
                    priority=task.priority,
                    deadline_slot=deadline_slot,
                    is_fixed=False,
                )
            )

        # Get the scheduler service and optimize
        service = SchedulerService(db)
        schedule_result = await service.optimize_schedule(
            UUID(user_id),
            task_inputs,
            date,
            num_days,
        )

        return {
            "success": schedule_result.success,
            "tasks_scheduled": len(tasks),
            "num_slots": schedule_result.num_slots,
            "message": f"Successfully rescheduled {len(tasks)} tasks"
            if schedule_result.success
            else schedule_result.error_message,
        }

    except Exception as e:
        logger.error(f"Failed to reschedule all: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Export all schedule management tools
SCHEDULE_TOOLS = [
    create_time_block,
    move_time_block,
    delete_time_block,
    get_optimized_schedule,
    get_weekly_timeline,
    reschedule_all,
]
