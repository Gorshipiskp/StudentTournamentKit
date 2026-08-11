"""game_servers registry

Revision ID: 0005_game_servers
Revises: 0004_judge_review
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_game_servers"
down_revision: str | None = "0004_judge_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "game_servers",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("endpoint_url", sa.String(length=512), nullable=True),
        sa.Column("webhook_secret", sa.String(length=128), nullable=True),
        sa.Column("assigned_match_id", sa.String(length=36), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bridge_version", sa.String(length=64), nullable=True),
        sa.Column("protocol_version", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_game_servers_assigned_match_id", "game_servers", ["assigned_match_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_game_servers_assigned_match_id", table_name="game_servers")
    op.drop_table("game_servers")
