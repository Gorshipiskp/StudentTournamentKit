"""game_commands + match.game_endpoint_url

Revision ID: 0003_game_commands
Revises: 0002_game_slice
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0003_game_commands"
down_revision: str | None = "0002_game_slice"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("game_endpoint_url", sa.String(length=512), nullable=True),
    )
    op.create_table(
        "game_commands",
        sa.Column("command_id", sa.String(length=36), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", mysql.JSON(), nullable=True),
        sa.Column("ack_status", sa.String(length=32), nullable=True),
        sa.Column("ack_error", sa.String(length=512), nullable=True),
        sa.Column("ack_result", mysql.JSON(), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ack_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("command_id"),
    )
    op.create_index("ix_game_commands_match_id", "game_commands", ["match_id"])


def downgrade() -> None:
    op.drop_index("ix_game_commands_match_id", table_name="game_commands")
    op.drop_table("game_commands")
    op.drop_column("matches", "game_endpoint_url")
