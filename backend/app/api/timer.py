"""
Timer REST API endpoints.

Implements:
- GET /api/timer/status - Current timer status
- POST /api/timer/start - Start timer
- POST /api/timer/stop - Stop timer
- GET /api/timer/analytics - Study analytics

Requirements: 15.2
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Subject, StudySession, ActiveTimer
from app.api.schemas import (
    TimerStatusSchema,
    StartTimerRequest,
    StopTimerResponse,
    TimerAnalyticsSchema,
    TimerAnalyticsResponse,
    StudySessionSchema,
)
from app.api.schedule import get_current_user

router = APIRouter(prefix="/timer", tags=["timer"])


@router.get("/status", response_model=TimerStatusSchema)
async def get_timer_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimerStatusSchema:
    """
    Get current timer status.

    Returns whether a timer is running and its details.
    """
    result = await db.execute(select(ActiveTimer).where(ActiveTimer.user_id == user.id))
    timer = result.scalar_one_or_none()

    if not timer:
        return TimerStatusSchema(is_running=False)

    # Get subject code if subject is set
    subject_code = None
    if timer.subject_id:
        subject_result = await db.execute(
            select(Subject).where(Subject.id == timer.subject_id)
        )
        subject = subject_result.scalar_one_or_none()
        if subject:
            subject_code = subject.code

    return TimerStatusSchema(
        is_running=True,
        subject_id=timer.subject_id,
        subject_code=subject_code,
        started_at=timer.started_at,
        elapsed_minutes=timer.elapsed_minutes,
    )


@router.post("/start", response_model=TimerStatusSchema)
async def start_timer(
    request: StartTimerRequest = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimerStatusSchema:
    """
    Start a study timer.

    Starts a new timer for the current user. Only one timer
    can be active at a time.
    """
    # Check if timer already running
    result = await db.execute(select(ActiveTimer).where(ActiveTimer.user_id == user.id))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Timer already running. Stop it first.",
        )

    # Validate subject if provided
    subject_code = None
    subject_id = request.subject_id if request else None

    if subject_id:
        subject_result = await db.execute(
            select(Subject).where(
                and_(
                    Subject.id == subject_id,
                    Subject.user_id == user.id,
                )
            )
        )
        subject = subject_result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=404,
                detail="Subject not found",
            )
        subject_code = subject.code

    # Create active timer
    timer = ActiveTimer(
        user_id=user.id,
        subject_id=subject_id,
        started_at=datetime.utcnow(),
    )

    db.add(timer)
    await db.commit()
    await db.refresh(timer)

    return TimerStatusSchema(
        is_running=True,
        subject_id=timer.subject_id,
        subject_code=subject_code,
        started_at=timer.started_at,
        elapsed_minutes=0,
    )


@router.post("/stop", response_model=StopTimerResponse)
async def stop_timer(
    notes: Optional[str] = Query(default=None, description="Session notes"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StopTimerResponse:
    """
    Stop the current timer.

    Stops the active timer and creates a study session record.
    Automatically calculates duration and deep work status.

    Property 15: Session Duration Auto-Calculation
    - duration_minutes = ended_at - started_at (in minutes)
    - is_deep_work = True if duration_minutes >= 90
    """
    # Get active timer
    result = await db.execute(select(ActiveTimer).where(ActiveTimer.user_id == user.id))
    timer = result.scalar_one_or_none()

    if not timer:
        raise HTTPException(
            status_code=400,
            detail="No timer running",
        )

    # Create study session
    session = StudySession(
        user_id=user.id,
        subject_id=timer.subject_id,
        started_at=timer.started_at,
        notes=notes,
    )

    # Stop the session - this calculates duration and deep work
    session.stop()

    db.add(session)

    # Delete active timer
    await db.delete(timer)

    await db.commit()
    await db.refresh(session)

    return StopTimerResponse(
        success=True,
        session_id=session.id,
        duration_minutes=session.duration_minutes,
        is_deep_work=session.is_deep_work,
    )


@router.get("/analytics", response_model=TimerAnalyticsResponse)
async def get_timer_analytics(
    period: str = Query(
        default="week", description="Analytics period: today, week, month"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TimerAnalyticsResponse:
    """
    Get study timer analytics.

    Returns aggregated study statistics for the specified period.
    """
    now = datetime.utcnow()

    # Calculate period start
    if period == "today":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        # Start of current week (Monday)
        days_since_monday = now.weekday()
        period_start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif period == "month":
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Use: today, week, month",
        )

    # Get sessions in period
    result = await db.execute(
        select(StudySession)
        .where(
            and_(
                StudySession.user_id == user.id,
                StudySession.started_at >= period_start,
                StudySession.ended_at.isnot(None),
            )
        )
        .order_by(StudySession.started_at.desc())
    )
    sessions = result.scalars().all()

    # Calculate analytics
    total_minutes = sum(s.duration_minutes or 0 for s in sessions)
    deep_work_minutes = sum(s.duration_minutes or 0 for s in sessions if s.is_deep_work)
    sessions_count = len(sessions)

    # Count unique subjects
    subject_ids = set(s.subject_id for s in sessions if s.subject_id)
    subjects_studied = len(subject_ids)

    # Calculate averages
    avg_session = total_minutes / sessions_count if sessions_count > 0 else 0
    longest_session = max((s.duration_minutes or 0 for s in sessions), default=0)

    # Calculate streak (consecutive days with study)
    streak_days = await _calculate_streak(db, user.id)

    # Get recent sessions (limit 10)
    recent_sessions = []
    for session in sessions[:10]:
        subject_code = None
        if session.subject_id:
            subj_result = await db.execute(
                select(Subject).where(Subject.id == session.subject_id)
            )
            subj = subj_result.scalar_one_or_none()
            if subj:
                subject_code = subj.code

        recent_sessions.append(
            StudySessionSchema(
                id=session.id,
                subject_id=session.subject_id,
                subject_code=subject_code,
                started_at=session.started_at,
                ended_at=session.ended_at,
                duration_minutes=session.duration_minutes,
                is_deep_work=session.is_deep_work,
                notes=session.notes,
            )
        )

    return TimerAnalyticsResponse(
        success=True,
        period=period,
        analytics=TimerAnalyticsSchema(
            total_study_minutes=total_minutes,
            deep_work_minutes=deep_work_minutes,
            sessions_count=sessions_count,
            subjects_studied=subjects_studied,
            average_session_minutes=round(avg_session, 1),
            longest_session_minutes=longest_session,
            streak_days=streak_days,
        ),
        recent_sessions=recent_sessions,
    )


async def _calculate_streak(db: AsyncSession, user_id: UUID) -> int:
    """Calculate consecutive days with study sessions."""
    today = datetime.utcnow().date()
    streak = 0
    current_date = today

    while True:
        # Check if there's a session on this date
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        result = await db.execute(
            select(StudySession.id)
            .where(
                and_(
                    StudySession.user_id == user_id,
                    StudySession.started_at >= day_start,
                    StudySession.started_at < day_end,
                    StudySession.ended_at.isnot(None),
                )
            )
            .limit(1)
        )

        if result.scalar_one_or_none():
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

        # Safety limit
        if streak > 365:
            break

    return streak
