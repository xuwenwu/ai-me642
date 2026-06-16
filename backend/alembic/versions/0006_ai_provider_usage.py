from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_ai_provider_usage"
down_revision = "0005_account_management"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "prompt_log_entries" not in existing_tables:
        return
    columns = _columns("prompt_log_entries")
    if "provider_input_tokens" not in columns:
        op.add_column("prompt_log_entries", sa.Column("provider_input_tokens", sa.Integer(), nullable=False, server_default="0"))
    if "provider_output_tokens" not in columns:
        op.add_column("prompt_log_entries", sa.Column("provider_output_tokens", sa.Integer(), nullable=False, server_default="0"))
    if "provider_total_tokens" not in columns:
        op.add_column("prompt_log_entries", sa.Column("provider_total_tokens", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "prompt_log_entries" not in existing_tables:
        return
    columns = _columns("prompt_log_entries")
    for column in ["provider_total_tokens", "provider_output_tokens", "provider_input_tokens"]:
        if column in columns:
            op.drop_column("prompt_log_entries", column)
