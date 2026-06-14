from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_account_management"
down_revision = "0004_phase10_controlled_ai"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "users" not in existing_tables:
        return
    columns = _columns("users")
    if "is_active" not in columns:
        op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    if "must_change_password" not in columns:
        op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "password_updated_at" not in columns:
        op.add_column("users", sa.Column("password_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "users" not in existing_tables:
        return
    columns = _columns("users")
    for column in ["password_updated_at", "must_change_password", "is_active"]:
        if column in columns:
            op.drop_column("users", column)
