from collections.abc import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


DEFAULT_ASSISTANT_SYSTEM_PROMPT = (
    "You are a cautious ME642 course assistant. Help students plan checks, debug reasoning, and "
    "interpret validation evidence. Do not fabricate simulation outputs, grades, or final scientific claims."
)


def _sqlite_columns(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def _ensure_local_sqlite_columns() -> None:
    if engine.dialect.name != "sqlite":
        return
    tables = set(inspect(engine).get_table_names())
    statements: list[str] = []
    if "ai_policies" in tables:
        columns = _sqlite_columns("ai_policies")
        if "assistant_enabled" not in columns:
            statements.append("ALTER TABLE ai_policies ADD COLUMN assistant_enabled BOOLEAN NOT NULL DEFAULT 0")
        if "assistant_provider" not in columns:
            statements.append("ALTER TABLE ai_policies ADD COLUMN assistant_provider VARCHAR(64) NOT NULL DEFAULT 'offline'")
        if "assistant_model" not in columns:
            statements.append("ALTER TABLE ai_policies ADD COLUMN assistant_model VARCHAR(128) NOT NULL DEFAULT ''")
        if "assistant_system_prompt" not in columns:
            statements.append(
                "ALTER TABLE ai_policies ADD COLUMN assistant_system_prompt TEXT NOT NULL DEFAULT "
                f"'{DEFAULT_ASSISTANT_SYSTEM_PROMPT}'"
            )
        if "assistant_retention_days" not in columns:
            statements.append("ALTER TABLE ai_policies ADD COLUMN assistant_retention_days INTEGER NOT NULL DEFAULT 180")
    if "prompt_log_entries" in tables:
        columns = _sqlite_columns("prompt_log_entries")
        if "provider_status" not in columns:
            statements.append("ALTER TABLE prompt_log_entries ADD COLUMN provider_status VARCHAR(64) NOT NULL DEFAULT 'manual'")
        if "provider_model" not in columns:
            statements.append("ALTER TABLE prompt_log_entries ADD COLUMN provider_model VARCHAR(128) NOT NULL DEFAULT ''")
        if "provider_response_id" not in columns:
            statements.append("ALTER TABLE prompt_log_entries ADD COLUMN provider_response_id VARCHAR(255) NOT NULL DEFAULT ''")
        if "privacy_flags_json" not in columns:
            statements.append("ALTER TABLE prompt_log_entries ADD COLUMN privacy_flags_json TEXT NOT NULL DEFAULT '[]'")
    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_local_sqlite_columns()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
