"""Task model for schedulable units of work."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import TaskPriority

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.subject import Subject
    from app.models.time_block import TimeBlock


class Task(Base, UUIDMixin, TimestampMixin):
    """Task model representing a schedulable unit of work."""

    __tablename__ = "tasks"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, default=TaskPriority.REGULAR_STUDY.value
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    subject: Mapped[Optional["Subject"]] = relationship(
        "Subject", back_populates="tasks"
    )
    time_blocks: Mapped[list["TimeBlock"]] = relationship(
        "TimeBlock", back_populates="task"
    )

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.deadline is None or self.is_completed:
            return False
        return datetime.utcnow() > self.deadline

    @property
    def effective_priority(self) -> int:
        """
        Get effective priority considering overdue status.

        Overdue tasks are automatically elevated to OVERDUE priority (100).
        """
        if self.is_overdue:
            return TaskPriority.OVERDUE.value
        return self.priority

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.is_completed = True
        self.completed_at = datetime.utcnow()

    def elevate_priority_if_overdue(self) -> bool:
        """
        Elevate priority to OVERDUE if task is overdue.

        Returns:
            True if priority was elevated, False otherwise
        """
        if self.is_overdue and self.priority < TaskPriority.OVERDUE.value:
            self.priority = TaskPriority.OVERDUE.value
            return True
        return False
