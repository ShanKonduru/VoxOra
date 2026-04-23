import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id"),
        nullable=False,
        index=True,
    )
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    transcript_raw: Mapped[str] = mapped_column(Text, nullable=False)
    transcript_clean: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    was_refocused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    refocus_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    moderation_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    moderation_categories: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped["Session"] = relationship("Session", back_populates="responses")
    question: Mapped["Question"] = relationship("Question", back_populates="responses")
