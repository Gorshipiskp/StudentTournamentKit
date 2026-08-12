"""tournaments: name, format, settings_json (TZ005 P1)

Revision ID: 0009_tournament_admin
Revises: 0008_invite_tokens
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0009_tournament_admin"
down_revision: str | None = "0008_invite_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "format",
            sa.String(length=32),
            nullable=False,
            server_default="single_elim",
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "settings_json",
            mysql.JSON(),
            nullable=False,
            server_default=sa.text("(CAST('{}' AS JSON))"),
        ),
    )


def downgrade() -> None:
    op.drop_column("tournaments", "settings_json")
    op.drop_column("tournaments", "format")
    op.drop_column("tournaments", "name")
