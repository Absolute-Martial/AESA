"""
Goals REST API endpoints.

Implements:
- GET /api/goals - List goals
- POST /api/goals - Create goal
- POST /api/goals/{id}/progress - Update progress
- GET /api/goals/summary/stats - Goal statistics

Requirements: 16.2, 16.3, 16.4
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, StudyGoal
from app.models.enums import GoalStatus
from app.api.schemas import (
    GoalSchema,
    GoalListResponse,
    CreateGoalRequest,
    UpdateGoalProgressRequest,
    GoalStatsSchema,
    GoalSummaryResponse,
)
from app.api.schedule import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])


def _goal_to_schema(goal: StudyGoal) -> GoalSchema:
    """Convert StudyGoal model to schema."""
    return GoalSchema(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        target_value=goal.target_value,
        current_value=goal.current_value,
        unit=goal.unit,
        deadline=goal.deadline,
        status=goal.status,
        progress_percent=goal.progress_percent,
        category_id=goal.category_id,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


@router.get("", response_model=GoalListResponse)
async def list_goals(
    status: Optional[str] = Query(
        default=None, description="Filter by status: active, completed, abandoned"
    ),
    category_id: Optional[UUID] = Query(default=None, description="Filter by category"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalListResponse:
    """
    List study goals.

    Returns goals with optional filtering by status and category.
    """
    query = select(StudyGoal).where(StudyGoal.user_id == user.id)

    if status:
        query = query.where(StudyGoal.status == status)

    if category_id:
        query = query.where(StudyGoal.category_id == category_id)

    # Get total count
    count_result = await db.execute(
        select(func.count(StudyGoal.id)).where(StudyGoal.user_id == user.id)
    )
    total = count_result.scalar() or 0

    # Execute with pagination
    query = query.order_by(StudyGoal.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    goals = result.scalars().all()

    return GoalListResponse(
        success=True,
        goals=[_goal_to_schema(g) for g in goals],
        total=total,
    )


@router.post("", response_model=GoalSchema, status_code=201)
async def create_goal(
    request: CreateGoalRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalSchema:
    """
    Create a new study goal.

    Creates a goal with optional target value and deadline.
    """
    goal = StudyGoal(
        user_id=user.id,
        title=request.title,
        description=request.description,
        target_value=request.target_value,
        unit=request.unit,
        deadline=request.deadline,
        category_id=request.category_id,
        status=GoalStatus.ACTIVE.value,
    )

    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    return _goal_to_schema(goal)


@router.get("/{goal_id}", response_model=GoalSchema)
async def get_goal(
    goal_id: UUID = Path(..., description="Goal ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalSchema:
    """
    Get a specific goal by ID.
    """
    result = await db.execute(
        select(StudyGoal).where(
            and_(
                StudyGoal.id == goal_id,
                StudyGoal.user_id == user.id,
            )
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    return _goal_to_schema(goal)


@router.post("/{goal_id}/progress", response_model=GoalSchema)
async def update_goal_progress(
    goal_id: UUID = Path(..., description="Goal ID"),
    request: UpdateGoalProgressRequest = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalSchema:
    """
    Update goal progress.

    Updates the current progress value for a goal.
    Automatically marks goal as completed if target is reached.
    """
    result = await db.execute(
        select(StudyGoal).where(
            and_(
                StudyGoal.id == goal_id,
                StudyGoal.user_id == user.id,
            )
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    if goal.status != GoalStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot update progress on non-active goal",
        )

    # Update progress
    goal.update_progress(request.progress)

    await db.commit()
    await db.refresh(goal)

    return _goal_to_schema(goal)


@router.get("/summary/stats", response_model=GoalSummaryResponse)
async def get_goal_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalSummaryResponse:
    """
    Get goal summary statistics.

    Returns aggregated statistics about user's goals.
    """
    # Get all goals
    result = await db.execute(select(StudyGoal).where(StudyGoal.user_id == user.id))
    goals = result.scalars().all()

    total = len(goals)
    active = sum(1 for g in goals if g.status == GoalStatus.ACTIVE.value)
    completed = sum(1 for g in goals if g.status == GoalStatus.COMPLETED.value)
    abandoned = sum(1 for g in goals if g.status == GoalStatus.ABANDONED.value)

    # Calculate completion rate
    finished = completed + abandoned
    completion_rate = (completed / finished * 100) if finished > 0 else 0.0

    # Calculate average progress of active goals
    active_goals = [g for g in goals if g.status == GoalStatus.ACTIVE.value]
    avg_progress = (
        sum(g.progress_percent for g in active_goals) / len(active_goals)
        if active_goals
        else 0.0
    )

    return GoalSummaryResponse(
        success=True,
        stats=GoalStatsSchema(
            total_goals=total,
            active_goals=active,
            completed_goals=completed,
            abandoned_goals=abandoned,
            completion_rate=round(completion_rate, 1),
            average_progress=round(avg_progress, 1),
        ),
    )


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: UUID = Path(..., description="Goal ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    Delete a goal.
    """
    result = await db.execute(
        select(StudyGoal).where(
            and_(
                StudyGoal.id == goal_id,
                StudyGoal.user_id == user.id,
            )
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    await db.delete(goal)
    await db.commit()

    return {"success": True, "message": "Goal deleted"}


@router.patch("/{goal_id}/abandon", response_model=GoalSchema)
async def abandon_goal(
    goal_id: UUID = Path(..., description="Goal ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GoalSchema:
    """
    Mark a goal as abandoned.
    """
    result = await db.execute(
        select(StudyGoal).where(
            and_(
                StudyGoal.id == goal_id,
                StudyGoal.user_id == user.id,
            )
        )
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    goal.status = GoalStatus.ABANDONED.value

    await db.commit()
    await db.refresh(goal)

    return _goal_to_schema(goal)
