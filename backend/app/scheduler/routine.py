"""
Daily routine block generation.

This module generates time blocks for daily routine activities
like sleep, meals, and wake routines based on user preferences.

Requirements: 10.1, 10.2, 10.3
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserPreferences
from app.scheduler.gaps import TimeBlock


@dataclass
class RoutineConfig:
    """Configuration for daily routine."""

    sleep_start: time = time(23, 0)
    sleep_end: time = time(6, 0)
    wake_routine_mins: int = 30
    breakfast_mins: int = 30
    lunch_time: time = time(13, 0)
    dinner_time: time = time(19, 30)
    max_study_block_mins: int = 90
    min_break_after_study: int = 15

    # Default meal durations
    lunch_mins: int = 45
    dinner_mins: int = 45

    @classmethod
    def from_preferences(cls, prefs: Optional[UserPreferences]) -> "RoutineConfig":
        """
        Create RoutineConfig from UserPreferences.

        Args:
            prefs: User preferences from database

        Returns:
            RoutineConfig with user's settings or defaults
        """
        if prefs is None:
            return cls()

        return cls(
            sleep_start=prefs.sleep_start or time(23, 0),
            sleep_end=prefs.sleep_end or time(6, 0),
            wake_routine_mins=prefs.wake_routine_mins or 30,
            breakfast_mins=prefs.breakfast_mins or 30,
            lunch_time=prefs.lunch_time or time(13, 0),
            dinner_time=prefs.dinner_time or time(19, 30),
            max_study_block_mins=prefs.max_study_block_mins or 90,
            min_break_after_study=prefs.min_break_after_study or 15,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "sleep_start": self.sleep_start.isoformat(),
            "sleep_end": self.sleep_end.isoformat(),
            "wake_routine_mins": self.wake_routine_mins,
            "breakfast_mins": self.breakfast_mins,
            "lunch_time": self.lunch_time.isoformat(),
            "dinner_time": self.dinner_time.isoformat(),
            "max_study_block_mins": self.max_study_block_mins,
            "min_break_after_study": self.min_break_after_study,
        }


class RoutineGenerator:
    """Generates daily routine time blocks."""

    def __init__(self, config: RoutineConfig):
        """
        Initialize the routine generator.

        Args:
            config: Routine configuration
        """
        self.config = config

    def get_active_hours(self, date: datetime) -> tuple[datetime, datetime]:
        """
        Get the active hours for a day (wake to sleep).

        Args:
            date: The date to get active hours for

        Returns:
            Tuple of (day_start, day_end) datetimes
        """
        # Wake time is sleep_end + wake_routine
        wake_dt = datetime.combine(date.date(), self.config.sleep_end)
        wake_dt += timedelta(minutes=self.config.wake_routine_mins)

        # Sleep time
        sleep_dt = datetime.combine(date.date(), self.config.sleep_start)

        # Handle overnight sleep (sleep_start is before midnight)
        if self.config.sleep_start < self.config.sleep_end:
            # Sleep starts after midnight, so it's the next day
            sleep_dt += timedelta(days=1)

        return wake_dt, sleep_dt

    def generate_routine_blocks(self, date: datetime) -> list[TimeBlock]:
        """
        Generate all routine blocks for a day.

        Args:
            date: The date to generate blocks for

        Returns:
            List of TimeBlocks for routine activities
        """
        blocks: list[TimeBlock] = []

        # Sleep block (previous night to morning)
        sleep_end_dt = datetime.combine(date.date(), self.config.sleep_end)
        sleep_start_dt = datetime.combine(
            date.date() - timedelta(days=1), self.config.sleep_start
        )

        # Only add sleep block if it makes sense
        if sleep_start_dt < sleep_end_dt:
            blocks.append(
                TimeBlock(
                    start_time=sleep_start_dt,
                    end_time=sleep_end_dt,
                    is_fixed=True,
                    block_type="sleep",
                )
            )

        # Wake routine block
        wake_start = sleep_end_dt
        wake_end = wake_start + timedelta(minutes=self.config.wake_routine_mins)
        blocks.append(
            TimeBlock(
                start_time=wake_start,
                end_time=wake_end,
                is_fixed=True,
                block_type="wake_routine",
            )
        )

        # Breakfast block (after wake routine)
        breakfast_start = wake_end
        breakfast_end = breakfast_start + timedelta(minutes=self.config.breakfast_mins)
        blocks.append(
            TimeBlock(
                start_time=breakfast_start,
                end_time=breakfast_end,
                is_fixed=True,
                block_type="breakfast",
            )
        )

        # Lunch block
        lunch_start = datetime.combine(date.date(), self.config.lunch_time)
        lunch_end = lunch_start + timedelta(minutes=self.config.lunch_mins)
        blocks.append(
            TimeBlock(
                start_time=lunch_start,
                end_time=lunch_end,
                is_fixed=True,
                block_type="lunch",
            )
        )

        # Dinner block
        dinner_start = datetime.combine(date.date(), self.config.dinner_time)
        dinner_end = dinner_start + timedelta(minutes=self.config.dinner_mins)
        blocks.append(
            TimeBlock(
                start_time=dinner_start,
                end_time=dinner_end,
                is_fixed=True,
                block_type="dinner",
            )
        )

        # Evening sleep block (tonight)
        tonight_sleep_start = datetime.combine(date.date(), self.config.sleep_start)
        tonight_sleep_end = datetime.combine(
            date.date() + timedelta(days=1), self.config.sleep_end
        )

        # Handle case where sleep_start is after midnight
        if self.config.sleep_start < self.config.sleep_end:
            tonight_sleep_start = datetime.combine(
                date.date() + timedelta(days=1), self.config.sleep_start
            )

        blocks.append(
            TimeBlock(
                start_time=tonight_sleep_start,
                end_time=tonight_sleep_end,
                is_fixed=True,
                block_type="sleep",
            )
        )

        return blocks

    def get_study_constraints(self) -> dict:
        """
        Get study-related constraints from config.

        Returns:
            Dictionary with study constraints
        """
        return {
            "max_study_block_mins": self.config.max_study_block_mins,
            "min_break_after_study": self.config.min_break_after_study,
        }


async def load_user_routine_config(
    db: AsyncSession,
    user_id: UUID,
) -> RoutineConfig:
    """
    Load routine configuration for a user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        RoutineConfig with user's settings or defaults
    """
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()
    return RoutineConfig.from_preferences(prefs)


async def generate_daily_routine(
    db: AsyncSession,
    user_id: UUID,
    date: datetime,
) -> list[TimeBlock]:
    """
    Generate daily routine blocks for a user.

    Args:
        db: Database session
        user_id: User UUID
        date: The date to generate blocks for

    Returns:
        List of TimeBlocks for routine activities
    """
    config = await load_user_routine_config(db, user_id)
    generator = RoutineGenerator(config)
    return generator.generate_routine_blocks(date)
