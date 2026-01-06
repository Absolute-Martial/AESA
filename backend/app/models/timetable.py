"""KU Timetable model for university class schedule."""

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import ClassType

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.subject import Subject


class KUTimetable(Base, UUIDMixin):
    """KU Timetable entry for university class schedule."""

    __tablename__ = "ku_timetable"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 0=Sunday, 6=Saturday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    class_type: Mapped[str] = mapped_column(String(20), default=ClassType.LECTURE.value)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="timetable_entries")
    subject: Mapped["Subject"] = relationship(
        "Subject", back_populates="timetable_entries"
    )

    @property
    def duration_minutes(self) -> int:
        """Calculate class duration in minutes."""
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        delta = end_dt - start_dt
        return int(delta.total_seconds() / 60)
