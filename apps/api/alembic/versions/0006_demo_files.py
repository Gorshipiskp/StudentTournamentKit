"""demo_files durable metadata

Revision ID: 0006_demo_files
Revises: 0005_game_servers
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_demo_files"
down_revision: str | None = "0005_game_servers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demo_files",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("durable_uri", sa.String(length=1024), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("map_name", sa.String(length=64), nullable=True),
        sa.Column("source_uri", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_demo_files_match_id", "demo_files", ["match_id"])


def downgrade() -> None:
    op.drop_index("ix_demo_files_match_id", table_name="demo_files")
    op.drop_table("demo_files")
