from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_pilot_feedback"
down_revision = "0006_ai_provider_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "pilot_feedback" in existing_tables:
        return
    op.create_table(
        "pilot_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("page_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("contact_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("instructor_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pilot_feedback_user_id", "pilot_feedback", ["user_id"])
    op.create_index("ix_pilot_feedback_category", "pilot_feedback", ["category"])
    op.create_index("ix_pilot_feedback_severity", "pilot_feedback", ["severity"])
    op.create_index("ix_pilot_feedback_status", "pilot_feedback", ["status"])
    op.create_index("ix_pilot_feedback_created_at", "pilot_feedback", ["created_at"])


def downgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "pilot_feedback" in existing_tables:
        op.drop_table("pilot_feedback")
