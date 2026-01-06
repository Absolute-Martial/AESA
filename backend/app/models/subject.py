"""Subject and Chapter models."""

import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task
    from app.models.study import StudySession
    from app.models.timetable import KUTimetable


# Subject code pattern: 4 uppercase letters followed by 3 digits
SUBJECT_CODE_PATTERN = re.compile(r"^[A-Z]{4}[0-9]{3}$")


def validate_subject_code(code: str) -> bool:
    """
    Validate subject code format.

    Args:
        code: Subject code to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(SUBJECT_CODE_PATTERN.match(code))


class Subject(Base, UUIDMixin):
    """Subject model representing a university course."""

    __tablename__ = "subjects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subjects")
    chapters: Mapped[list["Chapter"]] = relationship(
        "Chapter", back_populates="subject", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="subject")
    study_sessions: Mapped[list["StudySession"]] = relationship(
        "StudySession", back_populates="subject"
    )
    timetable_entries: Mapped[list["KUTimetable"]] = relationship(
        "KUTimetable", back_populates="subject", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Unique constraint on user_id and code
        {"sqlite_autoincrement": True},
    )

    @validates("code")
    def validate_code(self, key: str, code: str) -> str:
        """Validate subject code format."""
        if not validate_subject_code(code):
            raise ValueError(
                f"Invalid subject code '{code}'. "
                "Must be 4 uppercase letters followed by 3 digits (e.g., MATH101)"
            )
        return code


class Chapter(Base, UUIDMixin):
    """Chapter within a subject."""

    __tablename__ = "chapters"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="chapters")
    progress: Mapped[list["ChapterProgress"]] = relationship(
        "ChapterProgress", back_populates="chapter", cascade="all, delete-orphan"
    )
    revision_schedules: Mapped[list["RevisionSchedule"]] = relationship(
        "RevisionSchedule", back_populates="chapter", cascade="all, delete-orphan"
    )


class ChapterProgress(Base, UUIDMixin):
    """Progress tracking for a chapter."""

    __tablename__ = "chapter_progress"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
    )
    progress_type: Mapped[str] = mapped_column(String(50), nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    last_activity: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="progress")


class RevisionSchedule(Base, UUIDMixin):
    """Spaced repetition revision schedule."""

    __tablename__ = "revision_schedule"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_date: Mapped[datetime] = mapped_column(nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    chapter: Mapped["Chapter"] = relationship(
        "Chapter", back_populates="revision_schedules"
    )
