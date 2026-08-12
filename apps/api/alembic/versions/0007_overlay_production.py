"""overlay_states + production_sessions

Revision ID: 0007_overlay_production
Revises: 0006_demo_files
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0007_overlay_production"
down_revision: str | None = "0006_demo_files"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "overlay_states",
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("scene", sa.String(length=32), nullable=False),
        sa.Column("data_json", mysql.JSON(), nullable=False),
        sa.Column("manual_overrides", mysql.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("match_id"),
    )
    op.create_table(
        "production_sessions",
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("desired_scene", sa.String(length=32), nullable=False),
        sa.Column("actual_scene", sa.String(length=32), nullable=True),
        sa.Column("desired_stream", sa.String(length=16), nullable=False),
        sa.Column("actual_stream", sa.String(length=16), nullable=False),
        sa.Column("agent_status", sa.String(length=32), nullable=False),
        sa.Column("obs_status", sa.String(length=32), nullable=False),
        sa.Column("broadcast_status", sa.String(length=32), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("match_id"),
    )


def downgrade() -> None:
    op.drop_table("production_sessions")
    op.drop_table("overlay_states")
