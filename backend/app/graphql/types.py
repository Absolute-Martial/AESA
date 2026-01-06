"""GraphQL types for AESA using Strawberry."""

from datetime import datetime
from enum import Enum
from typing import Optional

import strawberry


# ============================================================================
# Enums
# ============================================================================


@strawberry.enum(description="Task type enumeration")
class TaskTypeEnum(Enum):
    """Task type enumeration for GraphQL."""

    UNIVERSITY = "university"
    STUDY = "study"
    REVISION = "revision"
    PRACTICE = "practice"
    ASSIGNMENT = "assignment"
    LAB_WORK = "lab_work"
    DEEP_WORK = "deep_work"
    BREAK = "break"
    FREE_TIME = "free_time"
    SLEEP = "sleep"
    WAKE_ROUTINE = "wake_routine"
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


@strawberry.enum(description="Goal status enumeration")
class GoalStatusEnum(Enum):
    """Goal status enumeration for GraphQL."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@strawberry.enum(description="Notification type enumeration")
class NotificationTypeEnum(Enum):
    """Notification type enumeration for GraphQL."""

    REMINDER = "reminder"
    SUGGESTION = "suggestion"
    ACHIEVEMENT = "achievement"
    WARNING = "warning"
    MOTIVATION = "motivation"


@strawberry.enum(description="Analytics period enumeration")
class AnalyticsPeriod(Enum):
    """Analytics period enumeration."""

    TODAY = "today"
    WEEK = "week"
    MONTH = "month"


@strawberry.enum(description="Gap type enumeration")
class GapType(Enum):
    """Gap type enumeration."""

    MICRO = "micro"
    STANDARD = "standard"
    DEEP_WORK = "deep_work"


# ============================================================================
# Core Types
# ============================================================================


@strawberry.type(description="A university subject/course")
class Subject:
    """Subject type representing a university course."""

    id: strawberry.ID
    code: str
    name: str
    color: Optional[str] = None
    created_at: datetime | None = None


@strawberry.type(description="A schedulable task")
class Task:
    """Task type representing a schedulable unit of work."""

    id: strawberry.ID
    title: str
    description: Optional[str] = None
    task_type: str
    duration_minutes: int
    priority: int
    deadline: Optional[datetime] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    subject_id: Optional[strawberry.ID] = None
    subject: Optional[Subject] = None
    created_at: datetime
    updated_at: datetime


@strawberry.type(description="A scheduled time block in the calendar")
class TimeBlock:
    """TimeBlock type representing a scheduled activity."""

    id: strawberry.ID
    title: str
    block_type: str
    start_time: datetime
    end_time: datetime
    is_fixed: bool
    task_id: Optional[strawberry.ID] = None
    task: Optional[Task] = None
    metadata: Optional[strawberry.scalars.JSON] = None
    duration_minutes: int


@strawberry.type(description="A gap in the schedule")
class Gap:
    """Gap type representing available time in the schedule."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int
    gap_type: str
    suggested_task_type: Optional[str] = None
    is_deep_work_opportunity: bool


@strawberry.type(description="Daily statistics")
class DayStats:
    """Statistics for a single day."""

    total_study_minutes: int
    deep_work_minutes: int
    has_deep_work_opportunity: bool
    gap_count: int
    tasks_completed: int
    energy_level: int


@strawberry.type(description="University timetable entry")
class TimetableEntry:
    """A university class entry in the timetable."""

    subject_code: str
    subject_name: str
    class_type: str
    start_time: str  # Time as string HH:MM
    end_time: str  # Time as string HH:MM
    room: Optional[str] = None


@strawberry.type(description="A persisted timetable slot (editable)")
class TimetableSlot:
    """Timetable slot backed by the KU timetable table."""

    id: strawberry.ID
    subject_id: strawberry.ID
    subject: Optional[Subject] = None
    day_of_week: int  # 0=Sunday, 6=Saturday
    start_time: str  # Time as string HH:MM
    end_time: str  # Time as string HH:MM
    room: Optional[str] = None
    class_type: str


@strawberry.input(description="Input for creating a timetable slot")
class CreateTimetableSlotInput:
    subject_id: strawberry.ID
    day_of_week: int
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    room: Optional[str] = None
    class_type: str = "lecture"


@strawberry.input(description="Input for updating a timetable slot")
class UpdateTimetableSlotInput:
    subject_id: Optional[strawberry.ID] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room: Optional[str] = None
    class_type: Optional[str] = None


@strawberry.input(description="Row for timetable CSV import")
class TimetableCsvRowInput:
    subject_code: str
    day_of_week: int
    start_time: str
    end_time: str
    room: Optional[str] = None
    class_type: Optional[str] = None


@strawberry.input(description="Input for importing timetable CSV")
class ImportTimetableCsvInput:
    rows: list[TimetableCsvRowInput]
    mode: str = "REPLACE"


@strawberry.type(description="Result of importing timetable CSV")
class ImportTimetableResult:
    created_count: int
    skipped_count: int
    errors: list[str]


@strawberry.type(description="Complete schedule for a day")
class DaySchedule:
    """Day schedule containing blocks, gaps, and stats."""

    schedule_date: str  # Date as string YYYY-MM-DD
    blocks: list[TimeBlock]
    gaps: list[Gap]
    classes: list[TimetableEntry]
    stats: DayStats

    @strawberry.field(description="Alias for scheduleDate (kept for backward compatibility)")
    def date(self) -> str:
        return self.schedule_date


@strawberry.type(description="Schedule for a week")
class WeekSchedule:
    """Week schedule containing multiple days."""

    start_date: str  # Date as string YYYY-MM-DD
    days: list[DaySchedule]


# ============================================================================
# Study & Timer Types
# ============================================================================


@strawberry.type(description="Study session record")
class StudySession:
    """A completed study session."""

    id: strawberry.ID
    subject_id: Optional[strawberry.ID] = None
    subject: Optional[Subject] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_deep_work: bool
    notes: Optional[str] = None


@strawberry.type(description="Current timer status")
class TimerStatus:
    """Status of the study timer."""

    is_running: bool
    subject_id: Optional[strawberry.ID] = None
    subject: Optional[Subject] = None
    started_at: Optional[datetime] = None
    elapsed_minutes: int


# ============================================================================
# Goal Types
# ============================================================================


@strawberry.type(description="A study goal")
class Goal:
    """Study goal with progress tracking."""

    id: strawberry.ID
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: float
    unit: Optional[str] = None
    deadline: Optional[str] = None  # Date as string YYYY-MM-DD
    status: str
    progress_percent: float
    category_id: Optional[strawberry.ID] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Notification Types
# ============================================================================


@strawberry.type(description="A user notification")
class Notification:
    """Notification for user alerts and reminders."""

    id: strawberry.ID
    notification_type: str
    title: str
    message: Optional[str] = None
    is_read: bool
    scheduled_for: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# Analytics Types
# ============================================================================


@strawberry.type(description="Study analytics data")
class StudyAnalytics:
    """Aggregated study analytics."""

    period: str
    total_study_minutes: int
    deep_work_minutes: int
    sessions_count: int
    subjects_studied: int
    average_session_minutes: float
    longest_session_minutes: int
    streak_days: int


# ============================================================================
# Chat Types
# ============================================================================


@strawberry.type(description="AI chat response")
class ChatResponse:
    """Response from AI chat."""

    message: str
    suggestions: list[str]
    tool_calls: list[str]


# ============================================================================
# Input Types
# ============================================================================


@strawberry.input(description="Input for creating a subject")
class CreateSubjectInput:
    code: str
    name: str
    color: Optional[str] = None


@strawberry.input(description="Input for updating a subject")
class UpdateSubjectInput:
    code: Optional[str] = None
    name: Optional[str] = None
    color: Optional[str] = None


@strawberry.input(description="Filter for task queries")
class TaskFilter:
    """Filter parameters for task queries."""

    task_type: Optional[str] = None
    is_completed: Optional[bool] = None
    subject_id: Optional[strawberry.ID] = None
    priority_min: Optional[int] = None
    priority_max: Optional[int] = None


@strawberry.input(description="Input for creating a task")
class CreateTaskInput:
    """Input for creating a new task."""

    title: str
    description: Optional[str] = None
    task_type: str = "study"
    duration_minutes: int
    priority: Optional[int] = 50
    deadline: Optional[datetime] = None
    subject_id: Optional[strawberry.ID] = None


@strawberry.input(description="Input for updating a task")
class UpdateTaskInput:
    """Input for updating an existing task."""

    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    priority: Optional[int] = None
    deadline: Optional[datetime] = None
    is_completed: Optional[bool] = None
    subject_id: Optional[strawberry.ID] = None


@strawberry.input(description="Input for creating a time block")
class CreateTimeBlockInput:
    """Input for creating a new time block."""

    title: str
    block_type: str = "study"
    start_time: datetime
    end_time: datetime
    is_fixed: bool = False
    task_id: Optional[strawberry.ID] = None


@strawberry.input(description="Input for creating a goal")
class CreateGoalInput:
    """Input for creating a new goal."""

    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    deadline: Optional[str] = None  # Date as string YYYY-MM-DD
    category_id: Optional[strawberry.ID] = None
