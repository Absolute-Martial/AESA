"""Study-related models: sessions, goals, stats, timer."""

import uuid
from datetime import datetime, date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, Text, Float, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import GoalStatus

if TYPE_CHECKING:
    from app.models.user import User, GoalCategory
    from app.models.subject import Subject


class StudySession(Base, UUIDMixin):
    """Study session tracking."""

    __tablename__ = "study_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_deep_work: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_sessions")
    subject: Mapped[Optional["Subject"]] = relationship(
        "Subject", back_populates="study_sessions"
    )

    def stop(self) -> None:
        """
        Stop the study session and calculate duration.

        Sets ended_at, calculates duration_minutes, and determines is_deep_work.
        """
        self.ended_at = datetime.utcnow()
        delta = self.ended_at - self.started_at
        self.duration_minutes = int(delta.total_seconds() / 60)
        # Deep work is 90+ minutes
        self.is_deep_work = self.duration_minutes >= 90


class ActiveTimer(Base):
    """Active timer for a user (one per user)."""

    __tablename__ = "active_timer"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="active_timer")
    subject: Mapped[Optional["Subject"]] = relationship("Subject")

    @property
    def elapsed_minutes(self) -> int:
        """Calculate elapsed time in minutes."""
        delta = datetime.utcnow() - self.started_at
        return int(delta.total_seconds() / 60)


class StudyGoal(Base, UUIDMixin, TimestampMixin):
    """Study goal with progress tracking."""

    __tablename__ = "study_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goal_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=GoalStatus.ACTIVE.value)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_goals")
    category: Mapped[Optional["GoalCategory"]] = relationship(
        "GoalCategory", back_populates="goals"
    )

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.target_value is None or self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def update_progress(self, value: float) -> None:
        """
        Update progress value.

        Args:
            value: New progress value
        """
        self.current_value = value
        if self.target_value and self.current_value >= self.target_value:
            self.status = GoalStatus.COMPLETED.value


class DailyStudyStats(Base, UUIDMixin, TimestampMixin):
    """Aggregated daily study statistics."""

    __tablename__ = "daily_study_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    deep_work_minutes: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    subjects_studied: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_stats")

    __table_args__ = (
        # Unique constraint on user_id and stat_date
        {"sqlite_autoincrement": True},
    )
