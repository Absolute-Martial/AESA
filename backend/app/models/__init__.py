"""SQLAlchemy models for AESA."""

from app.models.enums import (
    TaskType,
    TaskPriority,
    GoalStatus,
    NotificationType,
    LogLevel,
    ClassType,
    ProgressType,
)
from app.models.user import User, UserPreferences, GoalCategory
from app.models.assistant_settings import AssistantSettings
from app.models.subject import (
    Subject,
    Chapter,
    ChapterProgress,
    RevisionSchedule,
    validate_subject_code,
    SUBJECT_CODE_PATTERN,
)
from app.models.task import Task
from app.models.time_block import TimeBlock
from app.models.study import (
    StudySession,
    ActiveTimer,
    StudyGoal,
    DailyStudyStats,
)
from app.models.ai import AIMemory, AIGuideline
from app.models.notification import Notification
from app.models.timetable import KUTimetable
from app.models.log import SystemLog
from app.models.crud import CRUDBase

__all__ = [
    # Enums
    "TaskType",
    "TaskPriority",
    "GoalStatus",
    "NotificationType",
    "LogLevel",
    "ClassType",
    "ProgressType",
    # User models
    "User",
    "UserPreferences",
    "GoalCategory",
    "AssistantSettings",
    # Subject models
    "Subject",
    "Chapter",
    "ChapterProgress",
    "RevisionSchedule",
    "validate_subject_code",
    "SUBJECT_CODE_PATTERN",
    # Task models
    "Task",
    "TimeBlock",
    # Study models
    "StudySession",
    "ActiveTimer",
    "StudyGoal",
    "DailyStudyStats",
    # AI models
    "AIMemory",
    "AIGuideline",
    # Other models
    "Notification",
    "KUTimetable",
    "SystemLog",
    # CRUD
    "CRUDBase",
]
