from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_phase3_roster"
down_revision = "0001_initial_phase2"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existing_tables = _table_names()
    if "sections" not in existing_tables:
        op.create_table(
            "sections",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("term", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    if "enrollments" not in existing_tables:
        op.create_table(
            "enrollments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("section_id", sa.Integer(), sa.ForeignKey("sections.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False, server_default="student"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("course_id", "user_id", name="uq_enrollment_course_user"),
        )


def downgrade() -> None:
    existing_tables = _table_names()
    if "enrollments" in existing_tables:
        op.drop_table("enrollments")
    if "sections" in existing_tables:
        op.drop_table("sections")
