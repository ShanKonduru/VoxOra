import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id"),
        nullable=False,
        index=True,
    )
    # JSONB: {name, gender, accent, voice_id, greeting_style}
    persona: Mapped[dict] = mapped_column(JSONB, nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # GREETING | ASKING | LISTENING | PROCESSING | LOGGING | CLOSING | COMPLETED | TERMINATED
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="GREETING")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    flag_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    participant: Mapped["Participant"] = relationship(
        "Participant", back_populates="sessions"
    )
    responses: Mapped[list["Response"]] = relationship(
        "Response", back_populates="session", cascade="all, delete-orphan"
    )
