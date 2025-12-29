"""Enumeration types for the AESA models."""

from enum import Enum


class TaskType(str, Enum):
    """Task type enumeration - all 14 supported task types."""

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


class TaskPriority(int, Enum):
    """Task priority levels with numeric values."""

    FREE_TIME = 10
    REGULAR_STUDY = 50
    ASSIGNMENT = 60
    REVISION_DUE = 65
    URGENT_LAB = 75
    EXAM_PREP = 85
    DUE_TODAY = 90
    OVERDUE = 100


class GoalStatus(str, Enum):
    """Goal status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class NotificationType(str, Enum):
    """Notification type enumeration."""

    REMINDER = "reminder"
    SUGGESTION = "suggestion"
    ACHIEVEMENT = "achievement"
    WARNING = "warning"
    MOTIVATION = "motivation"


class LogLevel(str, Enum):
    """Log level enumeration."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ClassType(str, Enum):
    """University class type enumeration."""

    LECTURE = "lecture"
    LAB = "lab"


class ProgressType(str, Enum):
    """Chapter progress type enumeration."""

    READING = "reading"
    PRACTICE = "practice"
    REVISION = "revision"
