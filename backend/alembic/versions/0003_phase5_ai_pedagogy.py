from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_phase5_ai_pedagogy"
down_revision = "0002_phase3_roster"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing_tables = _table_names()
    if "ai_policies" not in existing_tables:
        op.create_table(
            "ai_policies",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False, unique=True),
            sa.Column("title", sa.String(length=255), nullable=False, server_default="Responsible AI Use Policy"),
            sa.Column("body", sa.Text(), nullable=False, server_default=""),
            sa.Column("allowed_tools_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("disclosure_requirements_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    if "prompt_templates" not in existing_tables:
        op.create_table(
            "prompt_templates",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("task_type", sa.String(length=64), nullable=False, server_default="lammps_debugging"),
            sa.Column("prompt_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("checklist_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )


def downgrade() -> None:
    existing_tables = _table_names()
    if "prompt_templates" in existing_tables:
        op.drop_table("prompt_templates")
    if "ai_policies" in existing_tables:
        op.drop_table("ai_policies")
