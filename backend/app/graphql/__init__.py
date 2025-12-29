"""GraphQL schema and resolvers for AESA."""

from app.graphql.schema import (
    schema,
    create_graphql_schema,
    create_graphql_router,
)
from app.graphql.types import (
    Task,
    TimeBlock,
    DaySchedule,
    WeekSchedule,
    Subject,
    Goal,
    Notification,
    TimerStatus,
    StudyAnalytics,
    StudySession,
    ChatResponse,
    Gap,
    DayStats,
    TimetableEntry,
    TaskFilter,
    CreateTaskInput,
    UpdateTaskInput,
    CreateTimeBlockInput,
    CreateGoalInput,
    AnalyticsPeriod,
    GoalStatusEnum,
    TaskTypeEnum,
    NotificationTypeEnum,
    GapType,
)
from app.graphql.resolvers import Query, Mutation

__all__ = [
    # Schema
    "schema",
    "create_graphql_schema",
    "create_graphql_router",
    # Resolvers
    "Query",
    "Mutation",
    # Types
    "Task",
    "TimeBlock",
    "DaySchedule",
    "WeekSchedule",
    "Subject",
    "Goal",
    "Notification",
    "TimerStatus",
    "StudyAnalytics",
    "StudySession",
    "ChatResponse",
    "Gap",
    "DayStats",
    "TimetableEntry",
    # Input types
    "TaskFilter",
    "CreateTaskInput",
    "UpdateTaskInput",
    "CreateTimeBlockInput",
    "CreateGoalInput",
    # Enums
    "AnalyticsPeriod",
    "GoalStatusEnum",
    "TaskTypeEnum",
    "NotificationTypeEnum",
    "GapType",
]
