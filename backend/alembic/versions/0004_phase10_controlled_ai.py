from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_phase10_controlled_ai"
down_revision = "0003_phase5_ai_pedagogy"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "ai_policies" in existing_tables:
        columns = _columns("ai_policies")
        if "assistant_enabled" not in columns:
            op.add_column("ai_policies", sa.Column("assistant_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "assistant_provider" not in columns:
            op.add_column("ai_policies", sa.Column("assistant_provider", sa.String(length=64), nullable=False, server_default="offline"))
        if "assistant_model" not in columns:
            op.add_column("ai_policies", sa.Column("assistant_model", sa.String(length=128), nullable=False, server_default=""))
        if "assistant_system_prompt" not in columns:
            op.add_column(
                "ai_policies",
                sa.Column(
                    "assistant_system_prompt",
                    sa.Text(),
                    nullable=False,
                    server_default=(
                        "You are a cautious ME642 course assistant. Help students plan checks, debug reasoning, and "
                        "interpret validation evidence. Do not fabricate simulation outputs, grades, or final scientific claims."
                    ),
                ),
            )
        if "assistant_retention_days" not in columns:
            op.add_column("ai_policies", sa.Column("assistant_retention_days", sa.Integer(), nullable=False, server_default="180"))

    if "prompt_log_entries" in existing_tables:
        columns = _columns("prompt_log_entries")
        if "provider_status" not in columns:
            op.add_column("prompt_log_entries", sa.Column("provider_status", sa.String(length=64), nullable=False, server_default="manual"))
        if "provider_model" not in columns:
            op.add_column("prompt_log_entries", sa.Column("provider_model", sa.String(length=128), nullable=False, server_default=""))
        if "provider_response_id" not in columns:
            op.add_column("prompt_log_entries", sa.Column("provider_response_id", sa.String(length=255), nullable=False, server_default=""))
        if "privacy_flags_json" not in columns:
            op.add_column("prompt_log_entries", sa.Column("privacy_flags_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "prompt_log_entries" in existing_tables:
        columns = _columns("prompt_log_entries")
        for column in ["privacy_flags_json", "provider_response_id", "provider_model", "provider_status"]:
            if column in columns:
                op.drop_column("prompt_log_entries", column)
    if "ai_policies" in existing_tables:
        columns = _columns("ai_policies")
        for column in [
            "assistant_retention_days",
            "assistant_system_prompt",
            "assistant_model",
            "assistant_provider",
            "assistant_enabled",
        ]:
            if column in columns:
                op.drop_column("ai_policies", column)
