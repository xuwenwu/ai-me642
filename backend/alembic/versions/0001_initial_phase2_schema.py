from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.database import Base
from app import models  # noqa: F401


revision = "0001_initial_phase2"
down_revision = None
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = _table_names()
    if "assignments" not in existing_tables:
        Base.metadata.create_all(bind=bind)
        return

    assignment_columns = _columns("assignments")
    if "validation_profile" not in assignment_columns:
        op.add_column("assignments", sa.Column("validation_profile", sa.String(length=64), nullable=False, server_default="lammps_basic_health"))
    if "required_file_types_json" not in assignment_columns:
        op.add_column("assignments", sa.Column("required_file_types_json", sa.Text(), nullable=False, server_default='["lammps_input", "lammps_log"]'))
    if "optional_file_types_json" not in assignment_columns:
        op.add_column("assignments", sa.Column("optional_file_types_json", sa.Text(), nullable=False, server_default='["readme", "prompt_log", "python_analysis", "ovito_script", "figure"]'))
    if "validation_settings_json" not in assignment_columns:
        op.add_column("assignments", sa.Column("validation_settings_json", sa.Text(), nullable=False, server_default="{}"))
    if "interpretation_prompts_json" not in assignment_columns:
        op.add_column("assignments", sa.Column("interpretation_prompts_json", sa.Text(), nullable=False, server_default="[]"))

    if "validation_reports" in existing_tables and "validation_profile" not in _columns("validation_reports"):
        op.add_column("validation_reports", sa.Column("validation_profile", sa.String(length=64), nullable=False, server_default="lammps_basic_health"))

    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
