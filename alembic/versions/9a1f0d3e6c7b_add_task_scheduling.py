"""Add task scheduling fields and task runs

Revision ID: 9a1f0d3e6c7b
Revises: 7c2f3f2e9a4b
Create Date: 2025-10-14 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9a1f0d3e6c7b"
down_revision: Union[str, Sequence[str], None] = "7c2f3f2e9a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("schedule_type", sa.String(), nullable=True, server_default="once"))
    op.add_column("tasks", sa.Column("schedule_value", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("timezone", sa.String(), nullable=True, server_default="Africa/Accra"))
    op.add_column("tasks", sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("tasks", sa.Column("next_run_at", sa.DateTime(), nullable=True))
    op.add_column("tasks", sa.Column("updated_at", sa.DateTime(), nullable=True))

    op.create_table(
        "task_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("task_runs")
    op.drop_column("tasks", "updated_at")
    op.drop_column("tasks", "next_run_at")
    op.drop_column("tasks", "payload")
    op.drop_column("tasks", "timezone")
    op.drop_column("tasks", "schedule_value")
    op.drop_column("tasks", "schedule_type")
