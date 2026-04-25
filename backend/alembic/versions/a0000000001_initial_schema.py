"""initial schema — all 6 core tables

Revision ID: a0000000001
Revises:
Create Date: 2026-04-25 00:00:00.000000

Creates the complete initial schema for VoxOra:
  admin_users, surveys, questions, participants, sessions, responses

Column types reflect the state BEFORE the cross-db portability migration
(c3a8f2b1e7d4) so the full migration chain works correctly on a blank DB.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "a0000000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── admin_users ───────────────────────────────────────────────────────────
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_users_username"), "admin_users", ["username"], unique=True
    )

    # ── surveys ───────────────────────────────────────────────────────────────
    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── questions ─────────────────────────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column(
            "question_type", sa.String(length=50), nullable=False, server_default="open_ended"
        ),
        # ARRAY(Text) — converted to JSONB in migration c3a8f2b1e7d4
        sa.Column(
            "expected_topics",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
        ),
        sa.Column("follow_up_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["survey_id"], ["surveys.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("survey_id", "order_index", name="uq_survey_order"),
    )
    op.create_index(
        op.f("ix_questions_survey_id"), "questions", ["survey_id"], unique=False
    )

    # ── participants ──────────────────────────────────────────────────────────
    op.create_table(
        "participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="PENDING"
        ),
        sa.Column("invite_token", sa.String(length=512), nullable=False),
        sa.Column("invite_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reminder_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("last_reminded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_token"),
    )
    op.create_index(
        op.f("ix_participants_survey_id"), "participants", ["survey_id"], unique=False
    )
    op.create_index(
        op.f("ix_participants_status"), "participants", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_participants_invite_token"),
        "participants",
        ["invite_token"],
        unique=True,
    )

    # ── sessions ──────────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), nullable=False),
        # JSONB — label changed to JSON in migration c3a8f2b1e7d4
        sa.Column("persona", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "current_question_index", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "state", sa.String(length=50), nullable=False, server_default="GREETING"
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        # INET — converted to VARCHAR(45) in migration c3a8f2b1e7d4
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("flag_reason", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["participant_id"], ["participants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sessions_participant_id"),
        "sessions",
        ["participant_id"],
        unique=False,
    )

    # ── responses ─────────────────────────────────────────────────────────────
    op.create_table(
        "responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("transcript_raw", sa.Text(), nullable=False),
        sa.Column("transcript_clean", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.String(length=512), nullable=True),
        sa.Column("sentiment_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "was_refocused", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "refocus_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "moderation_flagged", sa.Boolean(), nullable=False, server_default="false"
        ),
        # JSONB — converted to JSON in migration c3a8f2b1e7d4
        sa.Column(
            "moderation_categories",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_responses_session_id"), "responses", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_responses_question_id"), "responses", ["question_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_responses_question_id"), table_name="responses")
    op.drop_index(op.f("ix_responses_session_id"), table_name="responses")
    op.drop_table("responses")

    op.drop_index(op.f("ix_sessions_participant_id"), table_name="sessions")
    op.drop_table("sessions")

    op.drop_index(op.f("ix_participants_invite_token"), table_name="participants")
    op.drop_index(op.f("ix_participants_status"), table_name="participants")
    op.drop_index(op.f("ix_participants_survey_id"), table_name="participants")
    op.drop_table("participants")

    op.drop_index(op.f("ix_questions_survey_id"), table_name="questions")
    op.drop_table("questions")

    op.drop_table("surveys")

    op.drop_index(op.f("ix_admin_users_username"), table_name="admin_users")
    op.drop_table("admin_users")
