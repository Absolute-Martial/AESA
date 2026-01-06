"""Scheduler module for AESA."""

from app.scheduler.bridge import (
    CSchedulerBridge,
    SchedulerError,
    SchedulerErrorCode,
    TaskInput,
    TimeSlotInput,
    TimeSlotOutput,
    ScheduleResult,
    get_scheduler_bridge,
)
from app.scheduler.gaps import (
    Gap,
    GapType,
    TimeBlock,
    find_gaps,
    find_deep_work_slots,
    classify_gap,
    suggest_task_type_for_gap,
    merge_overlapping_blocks,
    MICRO_GAP_MAX,
    STANDARD_GAP_MAX,
    DEEP_WORK_MIN,
    DEEP_WORK_IDEAL,
)
from app.scheduler.timetable import (
    TimetableEntry,
    TimetableLoader,
    python_weekday_to_timetable,
    timetable_day_to_python,
)
from app.scheduler.routine import (
    RoutineConfig,
    RoutineGenerator,
    load_user_routine_config,
    generate_daily_routine,
)
from app.scheduler.service import (
    DaySchedule,
    SchedulerService,
)
from app.scheduler.priority import (
    PriorityLevel,
    calculate_priority,
    is_task_overdue,
    should_elevate_priority,
    get_elevated_priority,
    elevate_overdue_tasks,
    elevate_due_today_tasks,
    get_tasks_sorted_by_priority,
    sort_tasks_by_priority,
    compare_task_priority,
)
from app.scheduler.analytics import (
    AnalyticsPeriod,
    StudyAnalytics,
    aggregate_sessions,
    get_analytics_for_period,
    calculate_streak,
    get_subject_breakdown,
    update_daily_stats,
)

__all__ = [
    # Bridge
    "CSchedulerBridge",
    "SchedulerError",
    "SchedulerErrorCode",
    "TaskInput",
    "TimeSlotInput",
    "TimeSlotOutput",
    "ScheduleResult",
    "get_scheduler_bridge",
    # Gaps
    "Gap",
    "GapType",
    "TimeBlock",
    "find_gaps",
    "find_deep_work_slots",
    "classify_gap",
    "suggest_task_type_for_gap",
    "merge_overlapping_blocks",
    "MICRO_GAP_MAX",
    "STANDARD_GAP_MAX",
    "DEEP_WORK_MIN",
    "DEEP_WORK_IDEAL",
    # Timetable
    "TimetableEntry",
    "TimetableLoader",
    "python_weekday_to_timetable",
    "timetable_day_to_python",
    # Routine
    "RoutineConfig",
    "RoutineGenerator",
    "load_user_routine_config",
    "generate_daily_routine",
    # Service
    "DaySchedule",
    "SchedulerService",
    # Priority
    "PriorityLevel",
    "calculate_priority",
    "is_task_overdue",
    "should_elevate_priority",
    "get_elevated_priority",
    "elevate_overdue_tasks",
    "elevate_due_today_tasks",
    "get_tasks_sorted_by_priority",
    "sort_tasks_by_priority",
    "compare_task_priority",
    # Analytics
    "AnalyticsPeriod",
    "StudyAnalytics",
    "aggregate_sessions",
    "get_analytics_for_period",
    "calculate_streak",
    "get_subject_breakdown",
    "update_daily_stats",
]
