"""Assistant settings stored per user."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssistantSettings(Base):
    """Per-user settings for the AI assistant provider."""

    __tablename__ = "assistant_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    base_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User", back_populates="assistant_settings")
