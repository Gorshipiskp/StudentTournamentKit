"""review_resolution on matches

Revision ID: 0004_judge_review
Revises: 0003_game_commands
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_judge_review"
down_revision: str | None = "0003_game_commands"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("review_resolution", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("matches", "review_resolution")
