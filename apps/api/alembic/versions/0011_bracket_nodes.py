"""bracket_nodes — single elim (TZ005 P3)

Revision ID: 0011_bracket_nodes
Revises: 0010_teams_players
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_bracket_nodes"
down_revision: str | None = "0010_teams_players"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bracket_nodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tournament_id", sa.String(length=36), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("team_a_id", sa.String(length=36), nullable=True),
        sa.Column("team_b_id", sa.String(length=36), nullable=True),
        sa.Column("source_a_node_id", sa.String(length=36), nullable=True),
        sa.Column("source_b_node_id", sa.String(length=36), nullable=True),
        sa.Column("match_id", sa.String(length=36), nullable=True),
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
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.ForeignKeyConstraint(["team_a_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["team_b_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tournament_id",
            "round",
            "position",
            name="uq_bracket_tournament_round_pos",
        ),
    )
    op.create_index("ix_bracket_nodes_tournament_id", "bracket_nodes", ["tournament_id"])
    op.create_index("ix_bracket_nodes_match_id", "bracket_nodes", ["match_id"])


def downgrade() -> None:
    op.drop_index("ix_bracket_nodes_match_id", table_name="bracket_nodes")
    op.drop_index("ix_bracket_nodes_tournament_id", table_name="bracket_nodes")
    op.drop_table("bracket_nodes")
