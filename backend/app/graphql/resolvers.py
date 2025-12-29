"""GraphQL resolvers for AESA."""

from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.graphql.types import (
    Task,
    TimeBlock,
    DaySchedule,
    Subject,
    Goal,
    Notification,
    TimerStatus,
    StudyAnalytics,
    StudySession,
    ChatResponse,
    DayStats,
    TaskFilter,
    CreateTaskInput,
    UpdateTaskInput,
    CreateTimeBlockInput,
    CreateGoalInput,
    AnalyticsPeriod,
    GoalStatusEnum,
)


# ============================================================================
# Helper Functions
# ============================================================================


def get_mock_user_id() -> UUID:
    """Get mock user ID for development. Replace with actual auth."""
    return UUID("00000000-0000-0000-0000-000000000001")


def create_empty_day_stats() -> DayStats:
    """Create empty day statistics."""
    return DayStats(
        total_study_minutes=0,
        deep_work_minutes=0,
        has_deep_work_opportunity=False,
        gap_count=0,
        tasks_completed=0,
        energy_level=50,
    )


def create_empty_day_schedule(target_date: date) -> DaySchedule:
    """Create an empty day schedule."""
    return DaySchedule(
        schedule_date=target_date.isoformat(),
        blocks=[],
        gaps=[],
        classes=[],
        stats=create_empty_day_stats(),
    )


# ============================================================================
# Query Resolvers
# ============================================================================


@strawberry.type(description="GraphQL Query type with all available queries")
class Query:
    """GraphQL Query type with all available queries."""

    @strawberry.field(description="Get today's schedule with blocks, gaps, and stats")
    async def today_schedule(self, info: Info) -> DaySchedule:
        """Get the schedule for today."""
        today = date.today()
        return create_empty_day_schedule(today)

    @strawberry.field(description="Get schedule for a week starting from a date")
    async def week_schedule(
        self,
        info: Info,
        start_date: str,
    ) -> list[DaySchedule]:
        """Get the schedule for a week."""
        start = date.fromisoformat(start_date)
        days = []
        for i in range(7):
            day_date = start + timedelta(days=i)
            days.append(create_empty_day_schedule(day_date))
        return days

    @strawberry.field(description="Get all tasks with optional filtering")
    async def tasks(
        self,
        info: Info,
        filter: Optional[TaskFilter] = None,
    ) -> list[Task]:
        """Get tasks with optional filtering."""
        return []

    @strawberry.field(description="Get a single task by ID")
    async def task(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> Optional[Task]:
        """Get a specific task by ID."""
        return None

    @strawberry.field(description="Get all subjects")
    async def subjects(self, info: Info) -> list[Subject]:
        """Get all subjects for the user."""
        return []

    @strawberry.field(description="Get goals with optional status filter")
    async def goals(
        self,
        info: Info,
        status: Optional[GoalStatusEnum] = None,
    ) -> list[Goal]:
        """Get goals with optional status filter."""
        return []

    @strawberry.field(description="Get study analytics for a period")
    async def analytics(
        self,
        info: Info,
        period: AnalyticsPeriod,
    ) -> StudyAnalytics:
        """Get study analytics for the specified period."""
        return StudyAnalytics(
            period=period.value,
            total_study_minutes=0,
            deep_work_minutes=0,
            sessions_count=0,
            subjects_studied=0,
            average_session_minutes=0.0,
            longest_session_minutes=0,
            streak_days=0,
        )

    @strawberry.field(description="Get notifications with optional unread filter")
    async def notifications(
        self,
        info: Info,
        unread_only: Optional[bool] = False,
    ) -> list[Notification]:
        """Get notifications for the user."""
        return []

    @strawberry.field(description="Get current timer status")
    async def timer_status(self, info: Info) -> Optional[TimerStatus]:
        """Get the current timer status."""
        return TimerStatus(
            is_running=False,
            subject_id=None,
            subject=None,
            started_at=None,
            elapsed_minutes=0,
        )


# ============================================================================
# Mutation Resolvers
# ============================================================================


@strawberry.type(description="GraphQL Mutation type with all available mutations")
class Mutation:
    """GraphQL Mutation type with all available mutations."""

    @strawberry.mutation(description="Create a new task")
    async def create_task(
        self,
        info: Info,
        input: CreateTaskInput,
    ) -> Task:
        """Create a new task."""
        now = datetime.utcnow()
        return Task(
            id=strawberry.ID("new-task-id"),
            title=input.title,
            description=input.description,
            task_type=input.task_type,
            duration_minutes=input.duration_minutes,
            priority=input.priority or 50,
            deadline=input.deadline,
            is_completed=False,
            completed_at=None,
            subject_id=input.subject_id,
            subject=None,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation(description="Update an existing task")
    async def update_task(
        self,
        info: Info,
        id: strawberry.ID,
        input: UpdateTaskInput,
    ) -> Task:
        """Update an existing task."""
        now = datetime.utcnow()
        return Task(
            id=id,
            title=input.title or "Updated Task",
            description=input.description,
            task_type=input.task_type or "study",
            duration_minutes=input.duration_minutes or 30,
            priority=input.priority or 50,
            deadline=input.deadline,
            is_completed=input.is_completed or False,
            completed_at=None,
            subject_id=input.subject_id,
            subject=None,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation(description="Delete a task")
    async def delete_task(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> bool:
        """Delete a task by ID."""
        return True

    @strawberry.mutation(description="Create a new time block")
    async def create_time_block(
        self,
        info: Info,
        input: CreateTimeBlockInput,
    ) -> TimeBlock:
        """Create a new time block."""
        duration = int((input.end_time - input.start_time).total_seconds() / 60)
        return TimeBlock(
            id=strawberry.ID("new-block-id"),
            title=input.title,
            block_type=input.block_type,
            start_time=input.start_time,
            end_time=input.end_time,
            is_fixed=input.is_fixed,
            task_id=input.task_id,
            task=None,
            duration_minutes=duration,
        )

    @strawberry.mutation(description="Move a time block to a new start time")
    async def move_time_block(
        self,
        info: Info,
        id: strawberry.ID,
        new_start: datetime,
    ) -> TimeBlock:
        """Move a time block to a new start time."""
        duration_minutes = 60
        new_end = new_start + timedelta(minutes=duration_minutes)
        return TimeBlock(
            id=id,
            title="Moved Block",
            block_type="study",
            start_time=new_start,
            end_time=new_end,
            is_fixed=False,
            task_id=None,
            task=None,
            duration_minutes=duration_minutes,
        )

    @strawberry.mutation(description="Delete a time block")
    async def delete_time_block(
        self,
        info: Info,
        id: strawberry.ID,
    ) -> bool:
        """Delete a time block by ID."""
        return True

    @strawberry.mutation(description="Start the study timer")
    async def start_timer(
        self,
        info: Info,
        subject_id: Optional[strawberry.ID] = None,
    ) -> TimerStatus:
        """Start the study timer."""
        return TimerStatus(
            is_running=True,
            subject_id=subject_id,
            subject=None,
            started_at=datetime.utcnow(),
            elapsed_minutes=0,
        )

    @strawberry.mutation(description="Stop the study timer")
    async def stop_timer(self, info: Info) -> StudySession:
        """Stop the study timer and create a session."""
        now = datetime.utcnow()
        started = now - timedelta(minutes=45)
        return StudySession(
            id=strawberry.ID("new-session-id"),
            subject_id=None,
            subject=None,
            started_at=started,
            ended_at=now,
            duration_minutes=45,
            is_deep_work=False,
            notes=None,
        )

    @strawberry.mutation(description="Create a new goal")
    async def create_goal(
        self,
        info: Info,
        input: CreateGoalInput,
    ) -> Goal:
        """Create a new goal."""
        now = datetime.utcnow()
        return Goal(
            id=strawberry.ID("new-goal-id"),
            title=input.title,
            description=input.description,
            target_value=input.target_value,
            current_value=0.0,
            unit=input.unit,
            deadline=input.deadline,
            status="active",
            progress_percent=0.0,
            category_id=input.category_id,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation(description="Update goal progress")
    async def update_goal_progress(
        self,
        info: Info,
        id: strawberry.ID,
        progress: float,
    ) -> Goal:
        """Update the progress of a goal."""
        now = datetime.utcnow()
        target = 100.0
        progress_percent = min(100.0, (progress / target) * 100) if target > 0 else 0.0
        status = "completed" if progress >= target else "active"
        return Goal(
            id=id,
            title="Updated Goal",
            description=None,
            target_value=target,
            current_value=progress,
            unit="hours",
            deadline=None,
            status=status,
            progress_percent=progress_percent,
            category_id=None,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation(description="Send a message to the AI assistant")
    async def send_chat_message(
        self,
        info: Info,
        message: str,
    ) -> ChatResponse:
        """Send a message to the AI assistant."""
        return ChatResponse(
            message="I'm here to help with your schedule! This is a placeholder response.",
            suggestions=["Create a study block", "View today's schedule"],
            tool_calls=[],
        )
