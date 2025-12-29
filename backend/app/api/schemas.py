"""Pydantic schemas for API request/response validation."""

from datetime import datetime, date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TaskType


# ============================================================================
# Base Schemas
# ============================================================================


class BaseResponse(BaseModel):
    """Base response schema with success flag."""

    success: bool = True


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str
    message: str
    suggestion: Optional[str] = None
    context: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: ErrorDetail


# ============================================================================
# Schedule Schemas
# ============================================================================


class GapSchema(BaseModel):
    """Gap in the schedule."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int
    gap_type: str
    suggested_task_type: Optional[str] = None
    is_deep_work_opportunity: bool = False


class TimeBlockSchema(BaseModel):
    """Time block in the schedule."""

    id: Optional[UUID] = None
    title: str
    block_type: str
    start_time: datetime
    end_time: datetime
    is_fixed: bool = False
    task_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class DayStatsSchema(BaseModel):
    """Daily statistics."""

    total_study_minutes: int = 0
    deep_work_minutes: int = 0
    has_deep_work_opportunity: bool = False
    gap_count: int = 0
    tasks_completed: int = 0
    energy_level: int = 50


class TimetableEntrySchema(BaseModel):
    """University timetable entry."""

    subject_code: str
    subject_name: str
    class_type: str
    start_time: time
    end_time: time
    room: Optional[str] = None


class DayScheduleSchema(BaseModel):
    """Complete schedule for a day."""

    date: date
    blocks: list[TimeBlockSchema] = []
    gaps: list[GapSchema] = []
    classes: list[TimetableEntrySchema] = []
    stats: DayStatsSchema


class WeekScheduleSchema(BaseModel):
    """Schedule for a week."""

    start_date: date
    days: list[DayScheduleSchema] = []


class OptimizeScheduleRequest(BaseModel):
    """Request to optimize schedule."""

    start_date: Optional[date] = None
    num_days: int = Field(default=7, ge=1, le=14)
    task_ids: Optional[list[UUID]] = None


class OptimizeScheduleResponse(BaseResponse):
    """Response from schedule optimization."""

    schedule: Optional[WeekScheduleSchema] = None
    message: str = ""


# ============================================================================
# Preferences Schemas
# ============================================================================


class UserPreferencesSchema(BaseModel):
    """User preferences for daily routine and study constraints."""

    sleep_start: time = time(23, 0)
    sleep_end: time = time(6, 0)
    wake_routine_mins: int = Field(default=30, ge=0, le=120)
    breakfast_mins: int = Field(default=30, ge=0, le=60)
    lunch_time: time = time(13, 0)
    dinner_time: time = time(19, 30)
    max_study_block_mins: int = Field(default=90, ge=30, le=180)
    min_break_after_study: int = Field(default=15, ge=5, le=60)
    preferences: Optional[dict] = None


class UpdatePreferencesRequest(BaseModel):
    """Request to update user preferences."""

    sleep_start: Optional[time] = None
    sleep_end: Optional[time] = None
    wake_routine_mins: Optional[int] = Field(default=None, ge=0, le=120)
    breakfast_mins: Optional[int] = Field(default=None, ge=0, le=60)
    lunch_time: Optional[time] = None
    dinner_time: Optional[time] = None
    max_study_block_mins: Optional[int] = Field(default=None, ge=30, le=180)
    min_break_after_study: Optional[int] = Field(default=None, ge=5, le=60)
    preferences: Optional[dict] = None


# ============================================================================
# Task Schemas
# ============================================================================


class TaskSchema(BaseModel):
    """Task schema for API responses."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    description: Optional[str] = None
    task_type: str
    duration_minutes: int
    priority: int
    deadline: Optional[datetime] = None
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    subject_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class CreateTaskRequest(BaseModel):
    """Request to create a task."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: str = Field(default="study")
    duration_minutes: int = Field(..., ge=5, le=480)
    priority: Optional[int] = Field(default=50, ge=0, le=100)
    deadline: Optional[datetime] = None
    subject_id: Optional[UUID] = None

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        valid_types = [t.value for t in TaskType]
        if v not in valid_types:
            raise ValueError(f"Invalid task type. Must be one of: {valid_types}")
        return v


class UpdateTaskRequest(BaseModel):
    """Request to update a task."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: Optional[str] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    deadline: Optional[datetime] = None
    is_completed: Optional[bool] = None
    subject_id: Optional[UUID] = None

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_types = [t.value for t in TaskType]
        if v not in valid_types:
            raise ValueError(f"Invalid task type. Must be one of: {valid_types}")
        return v


class TaskFilterParams(BaseModel):
    """Filter parameters for task listing."""

    task_type: Optional[str] = None
    is_completed: Optional[bool] = None
    subject_id: Optional[UUID] = None
    priority_min: Optional[int] = Field(default=None, ge=0, le=100)
    priority_max: Optional[int] = Field(default=None, ge=0, le=100)
    deadline_before: Optional[datetime] = None
    deadline_after: Optional[datetime] = None


class TaskListResponse(BaseResponse):
    """Response for task listing."""

    tasks: list[TaskSchema] = []
    total: int = 0


# ============================================================================
# Timeline/TimeBlock Schemas
# ============================================================================


class CreateTimeBlockRequest(BaseModel):
    """Request to create a time block."""

    title: str = Field(..., min_length=1, max_length=255)
    block_type: str = Field(default="study")
    start_time: datetime
    end_time: datetime
    is_fixed: bool = False
    task_id: Optional[UUID] = None
    metadata: Optional[dict] = None

    @field_validator("block_type")
    @classmethod
    def validate_block_type(cls, v: str) -> str:
        valid_types = [t.value for t in TaskType]
        if v not in valid_types:
            raise ValueError(f"Invalid block type. Must be one of: {valid_types}")
        return v


class UpdateTimeBlockRequest(BaseModel):
    """Request to update/move a time block."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    block_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_fixed: Optional[bool] = None
    task_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class TimeBlockResponse(BaseResponse):
    """Response for time block operations."""

    block: Optional[TimeBlockSchema] = None


class TimelineResponse(BaseResponse):
    """Response for timeline operations."""

    date: date
    blocks: list[TimeBlockSchema] = []
    gaps: list[GapSchema] = []


# ============================================================================
# Timer Schemas
# ============================================================================


class TimerStatusSchema(BaseModel):
    """Timer status schema."""

    is_running: bool = False
    subject_id: Optional[UUID] = None
    subject_code: Optional[str] = None
    started_at: Optional[datetime] = None
    elapsed_minutes: int = 0


class StartTimerRequest(BaseModel):
    """Request to start a timer."""

    subject_id: Optional[UUID] = None


class StopTimerResponse(BaseResponse):
    """Response from stopping a timer."""

    session_id: UUID
    duration_minutes: int
    is_deep_work: bool = False


class StudySessionSchema(BaseModel):
    """Study session schema."""

    model_config = {"from_attributes": True}

    id: UUID
    subject_id: Optional[UUID] = None
    subject_code: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_deep_work: bool = False
    notes: Optional[str] = None


class TimerAnalyticsSchema(BaseModel):
    """Timer analytics schema."""

    total_study_minutes: int = 0
    deep_work_minutes: int = 0
    sessions_count: int = 0
    subjects_studied: int = 0
    average_session_minutes: float = 0.0
    longest_session_minutes: int = 0
    streak_days: int = 0


class TimerAnalyticsResponse(BaseResponse):
    """Response for timer analytics."""

    period: str
    analytics: TimerAnalyticsSchema
    recent_sessions: list[StudySessionSchema] = []


# ============================================================================
# Goals Schemas
# ============================================================================


class GoalSchema(BaseModel):
    """Goal schema for API responses."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: float = 0.0
    unit: Optional[str] = None
    deadline: Optional[date] = None
    status: str = "active"
    progress_percent: float = 0.0
    category_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class CreateGoalRequest(BaseModel):
    """Request to create a goal."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_value: Optional[float] = Field(default=None, ge=0)
    unit: Optional[str] = Field(default=None, max_length=50)
    deadline: Optional[date] = None
    category_id: Optional[UUID] = None


class UpdateGoalProgressRequest(BaseModel):
    """Request to update goal progress."""

    progress: float = Field(..., ge=0)


class GoalListResponse(BaseResponse):
    """Response for goal listing."""

    goals: list[GoalSchema] = []
    total: int = 0


class GoalStatsSchema(BaseModel):
    """Goal statistics schema."""

    total_goals: int = 0
    active_goals: int = 0
    completed_goals: int = 0
    abandoned_goals: int = 0
    completion_rate: float = 0.0
    average_progress: float = 0.0


class GoalSummaryResponse(BaseResponse):
    """Response for goal summary statistics."""

    stats: GoalStatsSchema
