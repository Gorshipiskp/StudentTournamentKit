"""match_audit_log (TZ006 P3)

Revision ID: 0013_match_audit_log
Revises: 0012_tournament_branding
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0013_match_audit_log"
down_revision: str | None = "0012_tournament_branding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "match_audit_log",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("tournament_id", sa.String(length=36), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            mysql.JSON(),
            nullable=False,
            server_default=sa.text("(CAST('{}' AS JSON))"),
        ),
        sa.Column("result", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_audit_log_match_id", "match_audit_log", ["match_id"])
    op.create_index(
        "ix_match_audit_log_correlation_id",
        "match_audit_log",
        ["correlation_id"],
    )
    op.create_index(
        "ix_match_audit_log_created_at",
        "match_audit_log",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_match_audit_log_created_at", table_name="match_audit_log")
    op.drop_index("ix_match_audit_log_correlation_id", table_name="match_audit_log")
    op.drop_index("ix_match_audit_log_match_id", table_name="match_audit_log")
    op.drop_table("match_audit_log")
