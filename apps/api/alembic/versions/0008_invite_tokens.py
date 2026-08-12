"""invite_tokens — opaque hashed invites (F4)

Revision ID: 0008_invite_tokens
Revises: 0007_overlay_production
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_invite_tokens"
down_revision: str | None = "0007_overlay_production"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invite_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_invite_tokens_token_hash", "invite_tokens", ["token_hash"])
    op.create_index("ix_invite_tokens_match_id", "invite_tokens", ["match_id"])


def downgrade() -> None:
    op.drop_index("ix_invite_tokens_match_id", table_name="invite_tokens")
    op.drop_index("ix_invite_tokens_token_hash", table_name="invite_tokens")
    op.drop_table("invite_tokens")
