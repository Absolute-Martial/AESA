"""TimeBlock model for scheduled activities."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class TimeBlock(Base, UUIDMixin):
    """TimeBlock model representing a scheduled activity in the calendar."""

    __tablename__ = "time_blocks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    block_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="time_blocks")
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="time_blocks")

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def overlaps_with(self, other: "TimeBlock") -> bool:
        """
        Check if this block overlaps with another.

        Args:
            other: Another TimeBlock to check against

        Returns:
            True if blocks overlap, False otherwise
        """
        return self.start_time < other.end_time and self.end_time > other.start_time
