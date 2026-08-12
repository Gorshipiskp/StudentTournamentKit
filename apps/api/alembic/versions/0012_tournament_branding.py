"""tournament_branding BLOBs (TZ005 P4)

Revision ID: 0012_tournament_branding
Revises: 0011_bracket_nodes
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0012_tournament_branding"
down_revision: str | None = "0011_bracket_nodes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tournament_branding",
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("logo_blob", mysql.MEDIUMBLOB(), nullable=True),
        sa.Column("logo_content_type", sa.String(length=64), nullable=True),
        sa.Column("bg_blob", mysql.MEDIUMBLOB(), nullable=True),
        sa.Column("bg_content_type", sa.String(length=64), nullable=True),
        sa.Column(
            "colors_json",
            mysql.JSON(),
            nullable=False,
            server_default=sa.text("(CAST('{}' AS JSON))"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.PrimaryKeyConstraint("tournament_id"),
    )


def downgrade() -> None:
    op.drop_table("tournament_branding")
