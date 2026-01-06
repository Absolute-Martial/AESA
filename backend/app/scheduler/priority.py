"""
Task priority system for AESA scheduling.

This module implements the priority calculation and elevation logic
for tasks based on deadlines and task types.

Requirements: 4.1, 4.3, 4.4
"""

from datetime import datetime
from enum import IntEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task


class PriorityLevel(IntEnum):
    """
    Task priority levels with numeric values.

    Higher values indicate higher priority.
    Requirements: 4.1
    """

    FREE_TIME = 10
    REGULAR_STUDY = 50
    ASSIGNMENT = 60
    REVISION_DUE = 65
    URGENT_LAB = 75
    EXAM_PREP = 85
    DUE_TODAY = 90
    OVERDUE = 100


def calculate_priority(
    task_type: str,
    deadline: Optional[datetime] = None,
    is_exam_related: bool = False,
    is_lab_urgent: bool = False,
) -> int:
    """
    Calculate priority for a task based on its attributes.

    Args:
        task_type: Type of task (study, assignment, etc.)
        deadline: Task deadline (if any)
        is_exam_related: Whether task is related to exam preparation
        is_lab_urgent: Whether task is an urgent lab report

    Returns:
        Priority value (0-100)
    """
    now = datetime.utcnow()

    # Check for overdue
    if deadline and deadline < now:
        return PriorityLevel.OVERDUE

    # Check for due today
    if deadline:
        deadline_date = deadline.date()
        today = now.date()
        if deadline_date == today:
            return PriorityLevel.DUE_TODAY

    # Check for exam prep
    if is_exam_related:
        return PriorityLevel.EXAM_PREP

    # Check for urgent lab
    if is_lab_urgent:
        return PriorityLevel.URGENT_LAB

    # Default priorities by task type
    type_priorities = {
        "assignment": PriorityLevel.ASSIGNMENT,
        "revision": PriorityLevel.REVISION_DUE,
        "lab_work": PriorityLevel.ASSIGNMENT,
        "study": PriorityLevel.REGULAR_STUDY,
        "practice": PriorityLevel.REGULAR_STUDY,
        "deep_work": PriorityLevel.REGULAR_STUDY,
        "free_time": PriorityLevel.FREE_TIME,
        "break": PriorityLevel.FREE_TIME,
    }

    return type_priorities.get(task_type, PriorityLevel.REGULAR_STUDY)


def is_task_overdue(deadline: Optional[datetime]) -> bool:
    """
    Check if a task is overdue.

    Args:
        deadline: Task deadline

    Returns:
        True if task is overdue, False otherwise
    """
    if deadline is None:
        return False
    return datetime.utcnow() > deadline


def should_elevate_priority(
    current_priority: int,
    deadline: Optional[datetime],
) -> bool:
    """
    Check if a task's priority should be elevated.

    Args:
        current_priority: Current priority value
        deadline: Task deadline

    Returns:
        True if priority should be elevated
    """
    if deadline is None:
        return False

    now = datetime.utcnow()

    # Elevate to OVERDUE if past deadline
    if deadline < now and current_priority < PriorityLevel.OVERDUE:
        return True

    # Elevate to DUE_TODAY if due today
    if deadline.date() == now.date() and current_priority < PriorityLevel.DUE_TODAY:
        return True

    return False


def get_elevated_priority(deadline: Optional[datetime]) -> int:
    """
    Get the elevated priority value based on deadline.

    Args:
        deadline: Task deadline

    Returns:
        Elevated priority value
    """
    if deadline is None:
        return PriorityLevel.REGULAR_STUDY

    now = datetime.utcnow()

    if deadline < now:
        return PriorityLevel.OVERDUE

    if deadline.date() == now.date():
        return PriorityLevel.DUE_TODAY

    return PriorityLevel.REGULAR_STUDY


async def elevate_overdue_tasks(db: AsyncSession, user_id: UUID) -> int:
    """
    Elevate priority of all overdue tasks for a user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Number of tasks elevated
    """
    now = datetime.utcnow()

    # Find overdue tasks with priority < OVERDUE
    result = await db.execute(
        update(Task)
        .where(
            Task.user_id == user_id,
            Task.deadline < now,
            ~Task.is_completed,
            Task.priority < PriorityLevel.OVERDUE,
        )
        .values(priority=PriorityLevel.OVERDUE)
    )

    return result.rowcount


async def elevate_due_today_tasks(db: AsyncSession, user_id: UUID) -> int:
    """
    Elevate priority of tasks due today for a user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Number of tasks elevated
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59)

    # Find tasks due today with priority < DUE_TODAY
    result = await db.execute(
        update(Task)
        .where(
            Task.user_id == user_id,
            Task.deadline >= today_start,
            Task.deadline <= today_end,
            ~Task.is_completed,
            Task.priority < PriorityLevel.DUE_TODAY,
        )
        .values(priority=PriorityLevel.DUE_TODAY)
    )

    return result.rowcount


async def get_tasks_sorted_by_priority(
    db: AsyncSession,
    user_id: UUID,
    include_completed: bool = False,
    limit: int = 100,
) -> list[Task]:
    """
    Get tasks sorted by priority (descending).

    Args:
        db: Database session
        user_id: User UUID
        include_completed: Whether to include completed tasks
        limit: Maximum number of tasks to return

    Returns:
        List of tasks sorted by priority (highest first)
    """
    query = select(Task).where(Task.user_id == user_id)

    if not include_completed:
        query = query.where(~Task.is_completed)

    query = query.order_by(Task.priority.desc()).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


def sort_tasks_by_priority(tasks: list[Task]) -> list[Task]:
    """
    Sort a list of tasks by effective priority (descending).

    Uses effective_priority which considers overdue status.

    Args:
        tasks: List of tasks to sort

    Returns:
        Sorted list of tasks (highest priority first)
    """
    return sorted(tasks, key=lambda t: t.effective_priority, reverse=True)


def compare_task_priority(task_a: Task, task_b: Task) -> int:
    """
    Compare two tasks by priority.

    Args:
        task_a: First task
        task_b: Second task

    Returns:
        Negative if task_a has higher priority,
        Positive if task_b has higher priority,
        Zero if equal
    """
    return task_b.effective_priority - task_a.effective_priority
