"""convert expected_topics ARRAY to JSON for cross-db compatibility
Revision ID: c3a8f2b1e7d4
Revises: b7f2c1a4d9e8
Create Date: 2026-04-25 00:00:00.000000

Also converts JSONB columns (persona, moderation_categories) to JSON and
INET (ip_address) to VARCHAR(45) for portability.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c3a8f2b1e7d4"
down_revision = "b7f2c1a4d9e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE questions "
        "ALTER COLUMN expected_topics TYPE JSONB "
        "USING to_jsonb(expected_topics)"
    )
    # sessions.persona JSONB → JSON (identical on-disk; label change only)
    op.alter_column("sessions", "persona", type_=sa.JSON())
    # sessions.ip_address INET → VARCHAR(45)
    op.execute(
        "ALTER TABLE sessions "
        "ALTER COLUMN ip_address TYPE VARCHAR(45) "
        "USING host(ip_address)"
    )
    # responses.moderation_categories JSONB → JSON
    op.alter_column("responses", "moderation_categories", type_=sa.JSON())


def downgrade() -> None:
    op.execute(
        "ALTER TABLE questions "
        "ALTER COLUMN expected_topics TYPE TEXT[] "
        "USING ARRAY(SELECT jsonb_array_elements_text(expected_topics))"
    )
    op.alter_column("sessions", "persona", type_=sa.dialects.postgresql.JSONB())
    op.execute(
        "ALTER TABLE sessions "
        "ALTER COLUMN ip_address TYPE INET "
        "USING ip_address::inet"
    )
    op.alter_column("responses", "moderation_categories", type_=sa.dialects.postgresql.JSONB())
