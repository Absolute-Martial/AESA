"""
KU Timetable configuration loading and processing.

This module handles loading and processing university class schedules
for integration with the scheduling system.

Requirements: 9.1, 9.2, 9.3
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KUTimetable, Subject
from app.scheduler.gaps import TimeBlock


@dataclass
class TimetableEntry:
    """Represents a single timetable entry."""

    subject_code: str
    subject_name: str
    day_of_week: int  # 0=Sunday, 6=Saturday
    start_time: time
    end_time: time
    room: Optional[str] = None
    class_type: str = "lecture"

    @property
    def duration_minutes(self) -> int:
        """Calculate class duration in minutes."""
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        delta = end_dt - start_dt
        return int(delta.total_seconds() / 60)

    def to_time_block(self, date: datetime) -> TimeBlock:
        """
        Convert to TimeBlock for a specific date.

        Args:
            date: The date to create the block for

        Returns:
            TimeBlock representing this class
        """
        start_dt = datetime.combine(date.date(), self.start_time)
        end_dt = datetime.combine(date.date(), self.end_time)

        return TimeBlock(
            start_time=start_dt,
            end_time=end_dt,
            is_fixed=True,
            block_type="university",
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "subject_code": self.subject_code,
            "subject_name": self.subject_name,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "room": self.room,
            "class_type": self.class_type,
            "duration_minutes": self.duration_minutes,
        }


class TimetableLoader:
    """Loads and processes KU timetable configuration."""

    # Day name mapping
    DAY_NAMES = {
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize the timetable loader.

        Args:
            db: Database session
        """
        self.db = db

    async def get_user_timetable(
        self,
        user_id: UUID,
    ) -> list[TimetableEntry]:
        """
        Get all timetable entries for a user.

        Args:
            user_id: User UUID

        Returns:
            List of timetable entries
        """
        result = await self.db.execute(
            select(KUTimetable, Subject)
            .join(Subject, KUTimetable.subject_id == Subject.id)
            .where(KUTimetable.user_id == user_id)
            .order_by(KUTimetable.day_of_week, KUTimetable.start_time)
        )

        entries = []
        for timetable, subject in result.all():
            entries.append(
                TimetableEntry(
                    subject_code=subject.code,
                    subject_name=subject.name,
                    day_of_week=timetable.day_of_week,
                    start_time=timetable.start_time,
                    end_time=timetable.end_time,
                    room=timetable.room,
                    class_type=timetable.class_type,
                )
            )

        return entries

    async def get_day_classes(
        self,
        user_id: UUID,
        day_of_week: int,
    ) -> list[TimetableEntry]:
        """
        Get classes for a specific day of the week.

        Args:
            user_id: User UUID
            day_of_week: Day of week (0=Sunday, 6=Saturday)

        Returns:
            List of timetable entries for that day
        """
        result = await self.db.execute(
            select(KUTimetable, Subject)
            .join(Subject, KUTimetable.subject_id == Subject.id)
            .where(
                KUTimetable.user_id == user_id,
                KUTimetable.day_of_week == day_of_week,
            )
            .order_by(KUTimetable.start_time)
        )

        entries = []
        for timetable, subject in result.all():
            entries.append(
                TimetableEntry(
                    subject_code=subject.code,
                    subject_name=subject.name,
                    day_of_week=timetable.day_of_week,
                    start_time=timetable.start_time,
                    end_time=timetable.end_time,
                    room=timetable.room,
                    class_type=timetable.class_type,
                )
            )

        return entries

    async def get_date_classes(
        self,
        user_id: UUID,
        date: datetime,
    ) -> list[TimetableEntry]:
        """
        Get classes for a specific date.

        Args:
            user_id: User UUID
            date: The date to get classes for

        Returns:
            List of timetable entries for that date
        """
        day_of_week = date.weekday()
        # Convert Python weekday (0=Monday) to our format (0=Sunday)
        day_of_week = (day_of_week + 1) % 7

        return await self.get_day_classes(user_id, day_of_week)

    async def get_date_time_blocks(
        self,
        user_id: UUID,
        date: datetime,
    ) -> list[TimeBlock]:
        """
        Get time blocks for classes on a specific date.

        Args:
            user_id: User UUID
            date: The date to get blocks for

        Returns:
            List of TimeBlocks for university classes
        """
        entries = await self.get_date_classes(user_id, date)
        return [entry.to_time_block(date) for entry in entries]

    def get_day_name(self, day_of_week: int) -> str:
        """Get the name of a day of the week."""
        return self.DAY_NAMES.get(day_of_week, "Unknown")


def python_weekday_to_timetable(weekday: int) -> int:
    """
    Convert Python weekday to timetable day format.

    Python: 0=Monday, 6=Sunday
    Timetable: 0=Sunday, 6=Saturday

    Args:
        weekday: Python weekday (0-6)

    Returns:
        Timetable day (0-6)
    """
    return (weekday + 1) % 7


def timetable_day_to_python(day: int) -> int:
    """
    Convert timetable day to Python weekday format.

    Timetable: 0=Sunday, 6=Saturday
    Python: 0=Monday, 6=Sunday

    Args:
        day: Timetable day (0-6)

    Returns:
        Python weekday (0-6)
    """
    return (day - 1) % 7
