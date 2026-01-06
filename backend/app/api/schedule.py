"""
Schedule REST API endpoints.

Implements:
- GET /api/schedule/today - Today's schedule with gaps
- GET /api/schedule/week - Week schedule
- POST /api/schedule/optimize - Trigger optimization
- GET /api/schedule/preferences - Get user preferences
- PUT /api/schedule/preferences - Update preferences

Requirements: 5.1, 10.4
"""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, UserPreferences, Task
from app.scheduler.service import SchedulerService, DaySchedule
from app.scheduler.bridge import SchedulerError, TaskInput
from app.api.schemas import (
    DayScheduleSchema,
    WeekScheduleSchema,
    DayStatsSchema,
    GapSchema,
    TimeBlockSchema,
    TimetableEntrySchema,
    OptimizeScheduleRequest,
    OptimizeScheduleResponse,
    UserPreferencesSchema,
    UpdatePreferencesRequest,
)

router = APIRouter(prefix="/schedule", tags=["schedule"])


# Temporary: Get or create a default user for development
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """Get current user (placeholder for auth)."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        # Create a default user for development
        user = User(
            email="dev@example.com",
            name="Development User",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


def _convert_day_schedule(schedule: DaySchedule) -> DayScheduleSchema:
    """Convert internal DaySchedule to API schema."""
    return DayScheduleSchema(
        date=schedule.date.date(),
        blocks=[
            TimeBlockSchema(
                title=getattr(b, "title", b.block_type),
                block_type=b.block_type,
                start_time=b.start_time,
                end_time=b.end_time,
                is_fixed=b.is_fixed,
            )
            for b in schedule.blocks
        ],
        gaps=[
            GapSchema(
                start_time=g.start_time,
                end_time=g.end_time,
                duration_minutes=g.duration_minutes,
                gap_type=g.gap_type.value,
                suggested_task_type=g.suggested_task_type,
                is_deep_work_opportunity=g.is_deep_work_opportunity,
            )
            for g in schedule.gaps
        ],
        classes=[
            TimetableEntrySchema(
                subject_code=c.subject_code,
                subject_name=c.subject_name,
                class_type=c.class_type.value,
                start_time=c.start_time,
                end_time=c.end_time,
                room=c.room,
            )
            for c in schedule.classes
        ],
        stats=DayStatsSchema(
            total_study_minutes=schedule.total_study_minutes,
            deep_work_minutes=schedule.deep_work_minutes,
            has_deep_work_opportunity=schedule.has_deep_work_opportunity,
            gap_count=len(schedule.gaps),
        ),
    )


@router.get("/today", response_model=DayScheduleSchema)
async def get_today_schedule(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DayScheduleSchema:
    """
    Get today's schedule with gaps and classes.

    Returns the complete schedule for today including:
    - Fixed blocks (classes, meals, sleep)
    - Available gaps for study
    - University classes
    - Daily statistics
    """
    service = SchedulerService(db)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    schedule = await service.get_day_schedule(user.id, today)
    return _convert_day_schedule(schedule)


@router.get("/week", response_model=WeekScheduleSchema)
async def get_week_schedule(
    start_date: Optional[date] = Query(
        default=None, description="Start date for the week (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeekScheduleSchema:
    """
    Get schedule for a week.

    Returns 7 days of schedule starting from the specified date
    or today if not specified.
    """
    service = SchedulerService(db)

    if start_date is None:
        start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_dt = datetime.combine(start_date, datetime.min.time())

    schedules = await service.get_week_schedule(user.id, start_dt)

    return WeekScheduleSchema(
        start_date=start_dt.date(),
        days=[_convert_day_schedule(s) for s in schedules],
    )


@router.post("/optimize", response_model=OptimizeScheduleResponse)
async def optimize_schedule(
    request: OptimizeScheduleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OptimizeScheduleResponse:
    """
    Trigger schedule optimization using the C engine.

    Optimizes task placement for the specified period using
    constraint satisfaction algorithms.
    """
    service = SchedulerService(db)

    # Determine start date
    if request.start_date is None:
        start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_dt = datetime.combine(request.start_date, datetime.min.time())

    # Get tasks to optimize
    query = select(Task).where(
        Task.user_id == user.id,
        ~Task.is_completed,
    )

    if request.task_ids:
        query = query.where(Task.id.in_(request.task_ids))

    result = await db.execute(query)
    tasks = result.scalars().all()

    if not tasks:
        return OptimizeScheduleResponse(
            success=True,
            message="No tasks to optimize",
            schedule=None,
        )

    # Convert tasks to TaskInput
    task_inputs = []
    for i, task in enumerate(tasks):
        # Calculate deadline slot if deadline exists
        deadline_slot = -1
        if task.deadline:
            days_until = (task.deadline.date() - start_dt.date()).days
            if days_until >= 0 and days_until < request.num_days:
                # Convert to slot index
                deadline_slot = (
                    days_until * 48
                    + (task.deadline.hour * 2)
                    + (task.deadline.minute // 30)
                )

        task_inputs.append(
            TaskInput(
                id=i,
                name=task.title,
                type=task.task_type,
                duration_slots=task.duration_minutes // 30,
                priority=task.effective_priority,
                deadline_slot=deadline_slot,
                is_fixed=False,
            )
        )

    try:
        # Run optimization
        result = await service.optimize_schedule(
            user_id=user.id,
            tasks=task_inputs,
            start_date=start_dt,
            num_days=request.num_days,
        )

        # Get updated schedule
        schedules = await service.get_week_schedule(user.id, start_dt)

        return OptimizeScheduleResponse(
            success=True,
            message=f"Optimized {len(tasks)} tasks for {request.num_days} days",
            schedule=WeekScheduleSchema(
                start_date=start_dt.date(),
                days=[_convert_day_schedule(s) for s in schedules[: request.num_days]],
            ),
        )
    except SchedulerError as e:
        return OptimizeScheduleResponse(
            success=False,
            message=e.message,
            schedule=None,
        )


@router.get("/preferences", response_model=UserPreferencesSchema)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserPreferencesSchema:
    """
    Get user's schedule preferences.

    Returns daily routine configuration and study constraints.
    """
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Return defaults
        return UserPreferencesSchema()

    return UserPreferencesSchema(
        sleep_start=prefs.sleep_start,
        sleep_end=prefs.sleep_end,
        wake_routine_mins=prefs.wake_routine_mins,
        breakfast_mins=prefs.breakfast_mins,
        lunch_time=prefs.lunch_time,
        dinner_time=prefs.dinner_time,
        max_study_block_mins=prefs.max_study_block_mins,
        min_break_after_study=prefs.min_break_after_study,
        preferences=prefs.preferences,
    )


@router.put("/preferences", response_model=UserPreferencesSchema)
async def update_preferences(
    request: UpdatePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserPreferencesSchema:
    """
    Update user's schedule preferences.

    Updates daily routine configuration and study constraints.
    Changes apply to future schedule optimizations.
    """
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Create new preferences
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)

    return UserPreferencesSchema(
        sleep_start=prefs.sleep_start,
        sleep_end=prefs.sleep_end,
        wake_routine_mins=prefs.wake_routine_mins,
        breakfast_mins=prefs.breakfast_mins,
        lunch_time=prefs.lunch_time,
        dinner_time=prefs.dinner_time,
        max_study_block_mins=prefs.max_study_block_mins,
        min_break_after_study=prefs.min_break_after_study,
        preferences=prefs.preferences,
    )
