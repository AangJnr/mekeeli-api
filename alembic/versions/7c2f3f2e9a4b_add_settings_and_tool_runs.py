"""Add settings and tool run tracking

Revision ID: 7c2f3f2e9a4b
Revises: a66a437fbcdf
Create Date: 2025-10-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7c2f3f2e9a4b"
down_revision: Union[str, Sequence[str], None] = "a66a437fbcdf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tools", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tools", sa.Column("requires_network", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("tools", sa.Column("input_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("tools", sa.Column("output_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("tools", sa.Column("danger_level", sa.String(), nullable=False, server_default="low"))

    op.create_table(
        "settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("offline_mode", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_text_model", sa.String(), nullable=True),
        sa.Column("default_vision_model", sa.String(), nullable=True),
        sa.Column("default_embed_model", sa.String(), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tool_permissions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tool_id", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("conversation_id", sa.String(), nullable=True),
        sa.Column("allowed", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_sessions.id"]),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tool_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tool_id", sa.String(), nullable=False),
        sa.Column("conversation_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_sessions.id"]),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tool_runs")
    op.drop_table("tool_permissions")
    op.drop_table("settings")
    op.drop_column("tools", "danger_level")
    op.drop_column("tools", "output_schema")
    op.drop_column("tools", "input_schema")
    op.drop_column("tools", "requires_network")
    op.drop_column("tools", "enabled")
