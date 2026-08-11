"""Game slice: match game fields + game_events dedup

Revision ID: 0002_game_slice
Revises: 0001_foundation
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0002_game_slice"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("score_team_a", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "matches",
        sa.Column("score_team_b", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "matches",
        sa.Column("round_number", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("matches", sa.Column("map_name", sa.String(length=64), nullable=True))
    op.add_column(
        "matches",
        sa.Column("phase", sa.String(length=32), nullable=False, server_default="warmup"),
    )
    op.add_column(
        "matches", sa.Column("game_server_id", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "matches",
        sa.Column("last_sequence", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "matches",
        sa.Column(
            "reconcile_needed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "matches",
        sa.Column(
            "actual_paused",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "matches",
        sa.Column(
            "desired_paused",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "matches", sa.Column("webhook_secret", sa.String(length=128), nullable=True)
    )
    op.create_index("ix_matches_game_server_id", "matches", ["game_server_id"])

    op.create_table(
        "game_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("server_id", sa.String(length=64), nullable=False),
        sa.Column("payload", mysql.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_game_events_match_id", "game_events", ["match_id"])


def downgrade() -> None:
    op.drop_index("ix_game_events_match_id", table_name="game_events")
    op.drop_table("game_events")
    op.drop_index("ix_matches_game_server_id", table_name="matches")
    op.drop_column("matches", "webhook_secret")
    op.drop_column("matches", "desired_paused")
    op.drop_column("matches", "actual_paused")
    op.drop_column("matches", "reconcile_needed")
    op.drop_column("matches", "last_sequence")
    op.drop_column("matches", "game_server_id")
    op.drop_column("matches", "phase")
    op.drop_column("matches", "map_name")
    op.drop_column("matches", "round_number")
    op.drop_column("matches", "score_team_b")
    op.drop_column("matches", "score_team_a")
