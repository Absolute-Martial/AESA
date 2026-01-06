"""User model and related entities."""

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Time, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.subject import Subject
    from app.models.task import Task
    from app.models.time_block import TimeBlock
    from app.models.study import StudySession, StudyGoal, DailyStudyStats, ActiveTimer
    from app.models.ai import AIMemory, AIGuideline
    from app.models.notification import Notification
    from app.models.timetable import KUTimetable
    from app.models.assistant_settings import AssistantSettings


class User(Base, UUIDMixin, TimestampMixin):
    """User model representing a student."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject", back_populates="user", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )
    time_blocks: Mapped[list["TimeBlock"]] = relationship(
        "TimeBlock", back_populates="user", cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(
        "StudySession", back_populates="user", cascade="all, delete-orphan"
    )
    study_goals: Mapped[list["StudyGoal"]] = relationship(
        "StudyGoal", back_populates="user", cascade="all, delete-orphan"
    )
    daily_stats: Mapped[list["DailyStudyStats"]] = relationship(
        "DailyStudyStats", back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ai_memories: Mapped[list["AIMemory"]] = relationship(
        "AIMemory", back_populates="user", cascade="all, delete-orphan"
    )
    ai_guidelines: Mapped[list["AIGuideline"]] = relationship(
        "AIGuideline", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    timetable_entries: Mapped[list["KUTimetable"]] = relationship(
        "KUTimetable", back_populates="user", cascade="all, delete-orphan"
    )
    active_timer: Mapped[Optional["ActiveTimer"]] = relationship(
        "ActiveTimer",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    goal_categories: Mapped[list["GoalCategory"]] = relationship(
        "GoalCategory", back_populates="user", cascade="all, delete-orphan"
    )
    assistant_settings: Mapped[Optional["AssistantSettings"]] = relationship(
        "AssistantSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserPreferences(Base):
    """User preferences for daily routine and study constraints."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Daily routine
    sleep_start: Mapped[time] = mapped_column(Time, default=time(23, 0))
    sleep_end: Mapped[time] = mapped_column(Time, default=time(6, 0))
    wake_routine_mins: Mapped[int] = mapped_column(Integer, default=30)
    breakfast_mins: Mapped[int] = mapped_column(Integer, default=30)
    lunch_time: Mapped[time] = mapped_column(Time, default=time(13, 0))
    dinner_time: Mapped[time] = mapped_column(Time, default=time(19, 30))

    # Study constraints
    max_study_block_mins: Mapped[int] = mapped_column(Integer, default=90)
    min_break_after_study: Mapped[int] = mapped_column(Integer, default=15)

    # Additional preferences as JSON
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")


class GoalCategory(Base, UUIDMixin):
    """Category for organizing study goals."""

    __tablename__ = "goal_categories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goal_categories")
    goals: Mapped[list["StudyGoal"]] = relationship(
        "StudyGoal", back_populates="category"
    )
