"""
Analytics aggregation module for study statistics.

Implements:
- Daily study stats aggregation
- Period-based filtering (today, week, month)
- Totals and metrics calculation

Requirements: 17.2, 17.3, 17.4, 17.5
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import StudySession, DailyStudyStats
from app.models.subject import Subject


class AnalyticsPeriod:
    """Analytics period definitions."""

    TODAY = "today"
    WEEK = "week"
    MONTH = "month"

    @classmethod
    def get_period_start(
        cls, period: str, reference_date: Optional[datetime] = None
    ) -> datetime:
        """
        Get the start datetime for a given period.

        Args:
            period: Period type (today, week, month)
            reference_date: Reference date (defaults to now)

        Returns:
            Start datetime for the period
        """
        now = reference_date or datetime.utcnow()

        if period == cls.TODAY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == cls.WEEK:
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            return (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif period == cls.MONTH:
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"Invalid period: {period}. Use: today, week, month")

    @classmethod
    def get_period_end(
        cls, period: str, reference_date: Optional[datetime] = None
    ) -> datetime:
        """
        Get the end datetime for a given period.

        Args:
            period: Period type (today, week, month)
            reference_date: Reference date (defaults to now)

        Returns:
            End datetime for the period
        """
        now = reference_date or datetime.utcnow()

        if period == cls.TODAY:
            return now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == cls.WEEK:
            # End of current week (Sunday)
            days_until_sunday = 6 - now.weekday()
            return (now + timedelta(days=days_until_sunday)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif period == cls.MONTH:
            # End of current month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            return (next_month - timedelta(days=1)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        else:
            raise ValueError(f"Invalid period: {period}. Use: today, week, month")


class StudyAnalytics:
    """
    Study analytics aggregation.

    Property 16: Analytics Aggregation Consistency
    For any analytics period (day, week, month), the total_study_time
    SHALL equal the sum of all individual session durations within that period.
    """

    def __init__(
        self,
        total_study_minutes: int = 0,
        deep_work_minutes: int = 0,
        sessions_count: int = 0,
        subjects_studied: int = 0,
        average_session_minutes: float = 0.0,
        longest_session_minutes: int = 0,
        streak_days: int = 0,
        tasks_completed: int = 0,
    ):
        self.total_study_minutes = total_study_minutes
        self.deep_work_minutes = deep_work_minutes
        self.sessions_count = sessions_count
        self.subjects_studied = subjects_studied
        self.average_session_minutes = average_session_minutes
        self.longest_session_minutes = longest_session_minutes
        self.streak_days = streak_days
        self.tasks_completed = tasks_completed

    @property
    def total_study_hours(self) -> float:
        """Get total study time in hours."""
        return round(self.total_study_minutes / 60, 2)

    @property
    def deep_work_hours(self) -> float:
        """Get deep work time in hours."""
        return round(self.deep_work_minutes / 60, 2)

    @property
    def deep_work_percentage(self) -> float:
        """Get percentage of study time that was deep work."""
        if self.total_study_minutes == 0:
            return 0.0
        return round((self.deep_work_minutes / self.total_study_minutes) * 100, 1)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_study_minutes": self.total_study_minutes,
            "deep_work_minutes": self.deep_work_minutes,
            "sessions_count": self.sessions_count,
            "subjects_studied": self.subjects_studied,
            "average_session_minutes": self.average_session_minutes,
            "longest_session_minutes": self.longest_session_minutes,
            "streak_days": self.streak_days,
            "tasks_completed": self.tasks_completed,
            "total_study_hours": self.total_study_hours,
            "deep_work_hours": self.deep_work_hours,
            "deep_work_percentage": self.deep_work_percentage,
        }


def aggregate_sessions(sessions: List[StudySession]) -> StudyAnalytics:
    """
    Aggregate study sessions into analytics.

    This function implements Property 16: Analytics Aggregation Consistency.
    The total_study_time equals the sum of all individual session durations.

    Args:
        sessions: List of study sessions to aggregate

    Returns:
        StudyAnalytics with aggregated metrics
    """
    if not sessions:
        return StudyAnalytics()

    # Calculate totals by summing individual session durations
    # Property 16: total_study_time = sum of all session durations
    total_minutes = sum(s.duration_minutes or 0 for s in sessions)
    deep_work_minutes = sum(s.duration_minutes or 0 for s in sessions if s.is_deep_work)

    sessions_count = len(sessions)

    # Count unique subjects
    subject_ids = set(s.subject_id for s in sessions if s.subject_id)
    subjects_studied = len(subject_ids)

    # Calculate averages
    avg_session = total_minutes / sessions_count if sessions_count > 0 else 0.0

    # Find longest session
    longest_session = max((s.duration_minutes or 0 for s in sessions), default=0)

    return StudyAnalytics(
        total_study_minutes=total_minutes,
        deep_work_minutes=deep_work_minutes,
        sessions_count=sessions_count,
        subjects_studied=subjects_studied,
        average_session_minutes=round(avg_session, 1),
        longest_session_minutes=longest_session,
    )


async def get_analytics_for_period(
    db: AsyncSession,
    user_id: UUID,
    period: str,
    reference_date: Optional[datetime] = None,
) -> StudyAnalytics:
    """
    Get aggregated analytics for a specific period.

    Implements Requirements 17.2, 17.3, 17.4, 17.5.

    Args:
        db: Database session
        user_id: User ID
        period: Period type (today, week, month)
        reference_date: Reference date for period calculation

    Returns:
        StudyAnalytics for the period
    """
    period_start = AnalyticsPeriod.get_period_start(period, reference_date)

    # Get all completed sessions in the period
    result = await db.execute(
        select(StudySession)
        .where(
            and_(
                StudySession.user_id == user_id,
                StudySession.started_at >= period_start,
                StudySession.ended_at.isnot(None),
            )
        )
        .order_by(StudySession.started_at.desc())
    )
    sessions = list(result.scalars().all())

    # Aggregate sessions
    analytics = aggregate_sessions(sessions)

    # Calculate streak
    analytics.streak_days = await calculate_streak(db, user_id)

    return analytics


async def calculate_streak(db: AsyncSession, user_id: UUID) -> int:
    """
    Calculate consecutive days with study sessions.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Number of consecutive days with study sessions
    """
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


async def get_subject_breakdown(
    db: AsyncSession,
    user_id: UUID,
    period: str,
    reference_date: Optional[datetime] = None,
) -> List[dict]:
    """
    Get study time breakdown by subject.

    Args:
        db: Database session
        user_id: User ID
        period: Period type (today, week, month)
        reference_date: Reference date for period calculation

    Returns:
        List of subject breakdowns with study time
    """
    period_start = AnalyticsPeriod.get_period_start(period, reference_date)

    # Get sessions grouped by subject
    result = await db.execute(
        select(
            StudySession.subject_id,
            func.sum(StudySession.duration_minutes).label("total_minutes"),
            func.count(StudySession.id).label("session_count"),
        )
        .where(
            and_(
                StudySession.user_id == user_id,
                StudySession.started_at >= period_start,
                StudySession.ended_at.isnot(None),
            )
        )
        .group_by(StudySession.subject_id)
    )

    rows = result.all()

    breakdown = []
    for row in rows:
        subject_id = row.subject_id
        total_minutes = row.total_minutes or 0
        session_count = row.session_count or 0

        # Get subject details if available
        subject_code = None
        subject_name = None
        if subject_id:
            subj_result = await db.execute(
                select(Subject).where(Subject.id == subject_id)
            )
            subject = subj_result.scalar_one_or_none()
            if subject:
                subject_code = subject.code
                subject_name = subject.name

        breakdown.append(
            {
                "subject_id": subject_id,
                "subject_code": subject_code or "Unassigned",
                "subject_name": subject_name or "No Subject",
                "total_minutes": total_minutes,
                "session_count": session_count,
            }
        )

    # Sort by total minutes descending
    breakdown.sort(key=lambda x: x["total_minutes"], reverse=True)

    return breakdown


async def update_daily_stats(
    db: AsyncSession,
    user_id: UUID,
    stat_date: date,
) -> DailyStudyStats:
    """
    Update or create daily study stats for a specific date.

    Args:
        db: Database session
        user_id: User ID
        stat_date: Date to update stats for

    Returns:
        Updated DailyStudyStats record
    """
    # Get all sessions for the date
    day_start = datetime.combine(stat_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    result = await db.execute(
        select(StudySession).where(
            and_(
                StudySession.user_id == user_id,
                StudySession.started_at >= day_start,
                StudySession.started_at < day_end,
                StudySession.ended_at.isnot(None),
            )
        )
    )
    sessions = list(result.scalars().all())

    # Calculate stats
    total_minutes = sum(s.duration_minutes or 0 for s in sessions)
    deep_work_minutes = sum(s.duration_minutes or 0 for s in sessions if s.is_deep_work)
    subject_ids = set(s.subject_id for s in sessions if s.subject_id)

    # Get or create daily stats record
    stats_result = await db.execute(
        select(DailyStudyStats).where(
            and_(
                DailyStudyStats.user_id == user_id,
                DailyStudyStats.stat_date == stat_date,
            )
        )
    )
    stats = stats_result.scalar_one_or_none()

    if stats:
        # Update existing
        stats.total_study_minutes = total_minutes
        stats.deep_work_minutes = deep_work_minutes
        stats.subjects_studied = len(subject_ids)
    else:
        # Create new
        stats = DailyStudyStats(
            user_id=user_id,
            stat_date=stat_date,
            total_study_minutes=total_minutes,
            deep_work_minutes=deep_work_minutes,
            subjects_studied=len(subject_ids),
        )
        db.add(stats)

    # Calculate streak
    stats.streak_days = await calculate_streak(db, user_id)

    await db.commit()
    await db.refresh(stats)

    return stats
