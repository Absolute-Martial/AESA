"""
Main scheduler service combining all scheduling components.

This module provides the high-level interface for schedule optimization,
combining gap detection, timetable loading, and routine generation.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduler.bridge import (
    CSchedulerBridge,
    TaskInput,
    TimeSlotInput,
    ScheduleResult,
    get_scheduler_bridge,
)
from app.scheduler.gaps import (
    Gap,
    GapType,
    TimeBlock,
    find_gaps,
    merge_overlapping_blocks,
)
from app.scheduler.timetable import TimetableLoader, TimetableEntry
from app.scheduler.routine import (
    RoutineConfig,
    RoutineGenerator,
    load_user_routine_config,
)


@dataclass
class DaySchedule:
    """Complete schedule for a day."""

    date: datetime
    blocks: list[TimeBlock]
    gaps: list[Gap]
    classes: list[TimetableEntry]
    routine_config: RoutineConfig

    @property
    def total_study_minutes(self) -> int:
        """Calculate total available study time."""
        return sum(gap.duration_minutes for gap in self.gaps)

    @property
    def deep_work_minutes(self) -> int:
        """Calculate total deep work time available."""
        return sum(
            gap.duration_minutes
            for gap in self.gaps
            if gap.gap_type == GapType.DEEP_WORK
        )

    @property
    def has_deep_work_opportunity(self) -> bool:
        """Check if there's a deep work opportunity (90+ min gap)."""
        return any(gap.is_deep_work_opportunity for gap in self.gaps)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "date": self.date.isoformat(),
            "blocks": [
                {
                    "start_time": b.start_time.isoformat(),
                    "end_time": b.end_time.isoformat(),
                    "is_fixed": b.is_fixed,
                    "block_type": b.block_type,
                }
                for b in self.blocks
            ],
            "gaps": [g.to_dict() for g in self.gaps],
            "classes": [c.to_dict() for c in self.classes],
            "stats": {
                "total_study_minutes": self.total_study_minutes,
                "deep_work_minutes": self.deep_work_minutes,
                "has_deep_work_opportunity": self.has_deep_work_opportunity,
                "gap_count": len(self.gaps),
            },
        }


class SchedulerService:
    """
    Main scheduler service for schedule optimization.

    Combines timetable loading, routine generation, gap detection,
    and C engine optimization into a unified interface.
    """

    def __init__(
        self,
        db: AsyncSession,
        bridge: Optional[CSchedulerBridge] = None,
    ):
        """
        Initialize the scheduler service.

        Args:
            db: Database session
            bridge: Optional C scheduler bridge (uses default if None)
        """
        self.db = db
        self.bridge = bridge or get_scheduler_bridge()
        self.timetable_loader = TimetableLoader(db)

    async def get_day_schedule(
        self,
        user_id: UUID,
        date: datetime,
    ) -> DaySchedule:
        """
        Get complete schedule for a day including gaps.

        Args:
            user_id: User UUID
            date: The date to get schedule for

        Returns:
            DaySchedule with blocks, gaps, and classes
        """
        # Load user's routine config
        routine_config = await load_user_routine_config(self.db, user_id)
        routine_generator = RoutineGenerator(routine_config)

        # Get active hours for the day
        day_start, day_end = routine_generator.get_active_hours(date)

        # Generate routine blocks
        routine_blocks = routine_generator.generate_routine_blocks(date)

        # Get university classes
        classes = await self.timetable_loader.get_date_classes(user_id, date)
        class_blocks = [c.to_time_block(date) for c in classes]

        # Combine all fixed blocks
        all_blocks = routine_blocks + class_blocks

        # Filter blocks to only those within active hours
        active_blocks = [
            b for b in all_blocks if b.end_time > day_start and b.start_time < day_end
        ]

        # Merge overlapping blocks
        merged_blocks = merge_overlapping_blocks(active_blocks)

        # Find gaps
        gaps = find_gaps(merged_blocks, day_start, day_end)

        return DaySchedule(
            date=date,
            blocks=merged_blocks,
            gaps=gaps,
            classes=classes,
            routine_config=routine_config,
        )

    async def get_week_schedule(
        self,
        user_id: UUID,
        start_date: datetime,
    ) -> list[DaySchedule]:
        """
        Get schedule for a week.

        Args:
            user_id: User UUID
            start_date: First day of the week

        Returns:
            List of DaySchedule for 7 days
        """
        schedules = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            schedule = await self.get_day_schedule(user_id, date)
            schedules.append(schedule)
        return schedules

    async def find_deep_work_opportunities(
        self,
        user_id: UUID,
        date: datetime,
        min_duration_minutes: int = 90,
    ) -> list[Gap]:
        """
        Find deep work opportunities for a day.

        Args:
            user_id: User UUID
            date: The date to search
            min_duration_minutes: Minimum gap duration

        Returns:
            List of gaps suitable for deep work
        """
        schedule = await self.get_day_schedule(user_id, date)
        return [
            gap for gap in schedule.gaps if gap.duration_minutes >= min_duration_minutes
        ]

    async def optimize_schedule(
        self,
        user_id: UUID,
        tasks: list[TaskInput],
        start_date: datetime,
        num_days: int = 7,
    ) -> ScheduleResult:
        """
        Optimize schedule using the C engine.

        Args:
            user_id: User UUID
            tasks: List of tasks to schedule
            start_date: First day to optimize
            num_days: Number of days to optimize

        Returns:
            Optimized schedule result from C engine
        """
        # Collect all fixed slots for the period
        fixed_slots: list[TimeSlotInput] = []

        for day_offset in range(num_days):
            date = start_date + timedelta(days=day_offset)
            schedule = await self.get_day_schedule(user_id, date)

            # Convert blocks to fixed slots
            for block in schedule.blocks:
                if block.is_fixed:
                    # Convert datetime to slot index
                    # Each slot is 30 minutes, starting from midnight
                    slot_index = self._datetime_to_slot_index(
                        block.start_time,
                        start_date,
                    )
                    duration_slots = block.duration_minutes // 30

                    # Add a fixed slot for each 30-minute period
                    for i in range(duration_slots):
                        fixed_slots.append(
                            TimeSlotInput(
                                slot_index=slot_index + i,
                                task_id=-1,  # No task, just blocked
                                is_fixed=True,
                            )
                        )

        # Call C engine
        return await self.bridge.optimize(
            tasks=tasks,
            fixed_slots=fixed_slots,
            num_days=num_days,
        )

    def _datetime_to_slot_index(
        self,
        dt: datetime,
        reference_date: datetime,
    ) -> int:
        """
        Convert datetime to slot index.

        Args:
            dt: Datetime to convert
            reference_date: Reference date (day 0)

        Returns:
            Slot index (0-based, 48 slots per day)
        """
        # Calculate days since reference
        days = (dt.date() - reference_date.date()).days

        # Calculate slots within the day
        minutes_since_midnight = dt.hour * 60 + dt.minute
        slots_in_day = minutes_since_midnight // 30

        # Total slot index
        return days * 48 + slots_in_day

    def _slot_index_to_datetime(
        self,
        slot_index: int,
        reference_date: datetime,
    ) -> datetime:
        """
        Convert slot index to datetime.

        Args:
            slot_index: Slot index to convert
            reference_date: Reference date (day 0)

        Returns:
            Datetime for the slot
        """
        days = slot_index // 48
        slots_in_day = slot_index % 48

        minutes = slots_in_day * 30
        hours = minutes // 60
        minutes = minutes % 60

        return datetime.combine(
            reference_date.date() + timedelta(days=days),
            datetime.min.time().replace(hour=hours, minute=minutes),
        )
