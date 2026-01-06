"""
Task REST API endpoints.

Implements:
- GET /api/tasks - List tasks with filtering
- POST /api/tasks - Create task
- PATCH /api/tasks/{id} - Update task
- DELETE /api/tasks/{id} - Delete task

Requirements: 5.1
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Task
from app.scheduler.priority import sort_tasks_by_priority
from app.api.schemas import (
    TaskSchema,
    TaskListResponse,
    CreateTaskRequest,
    UpdateTaskRequest,
)
from app.api.schedule import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_schema(task: Task) -> TaskSchema:
    """Convert Task model to schema."""
    return TaskSchema(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        duration_minutes=task.duration_minutes,
        priority=task.effective_priority,
        deadline=task.deadline,
        is_completed=task.is_completed,
        completed_at=task.completed_at,
        subject_id=task.subject_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
    is_completed: Optional[bool] = Query(
        default=None, description="Filter by completion status"
    ),
    subject_id: Optional[UUID] = Query(default=None, description="Filter by subject"),
    priority_min: Optional[int] = Query(
        default=None, ge=0, le=100, description="Minimum priority"
    ),
    priority_max: Optional[int] = Query(
        default=None, ge=0, le=100, description="Maximum priority"
    ),
    deadline_before: Optional[datetime] = Query(
        default=None, description="Deadline before date"
    ),
    deadline_after: Optional[datetime] = Query(
        default=None, description="Deadline after date"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskListResponse:
    """
    List tasks with optional filtering.

    Returns tasks sorted by priority in descending order.
    Supports filtering by type, completion status, subject,
    priority range, and deadline range.
    """
    # Build query
    query = select(Task).where(Task.user_id == user.id)

    # Apply filters
    if task_type is not None:
        query = query.where(Task.task_type == task_type)

    if is_completed is not None:
        query = query.where(Task.is_completed == is_completed)

    if subject_id is not None:
        query = query.where(Task.subject_id == subject_id)

    if priority_min is not None:
        query = query.where(Task.priority >= priority_min)

    if priority_max is not None:
        query = query.where(Task.priority <= priority_max)

    if deadline_before is not None:
        query = query.where(Task.deadline <= deadline_before)

    if deadline_after is not None:
        query = query.where(Task.deadline >= deadline_after)

    # Get total count
    count_query = select(Task.id).where(Task.user_id == user.id)
    if task_type is not None:
        count_query = count_query.where(Task.task_type == task_type)
    if is_completed is not None:
        count_query = count_query.where(Task.is_completed == is_completed)

    count_result = await db.execute(count_query)
    total = len(count_result.all())

    # Execute query with pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    # Sort by priority (descending) - Property 10
    sorted_tasks = sort_tasks_by_priority(tasks)

    return TaskListResponse(
        success=True,
        tasks=[_task_to_schema(t) for t in sorted_tasks],
        total=total,
    )


@router.post("", response_model=TaskSchema, status_code=201)
async def create_task(
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskSchema:
    """
    Create a new task.

    Creates a schedulable task with the specified properties.
    """
    task = Task(
        user_id=user.id,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        duration_minutes=request.duration_minutes,
        priority=request.priority or 50,
        deadline=request.deadline,
        subject_id=request.subject_id,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return _task_to_schema(task)


@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
    task_id: UUID = Path(..., description="Task ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskSchema:
    """
    Get a specific task by ID.
    """
    result = await db.execute(
        select(Task).where(
            and_(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return _task_to_schema(task)


@router.patch("/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: UUID = Path(..., description="Task ID"),
    request: UpdateTaskRequest = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskSchema:
    """
    Update a task.

    Updates the specified task's properties.
    """
    result = await db.execute(
        select(Task).where(
            and_(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    if request:
        update_data = request.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                setattr(task, field, value)

        # Handle completion
        if "is_completed" in update_data and update_data["is_completed"]:
            task.mark_completed()

    await db.commit()
    await db.refresh(task)

    return _task_to_schema(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID = Path(..., description="Task ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    Delete a task.

    Removes the specified task from the system.
    """
    result = await db.execute(
        select(Task).where(
            and_(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    await db.delete(task)
    await db.commit()

    return {"success": True, "message": "Task deleted"}
