from __future__ import annotations

import shutil
import sys
import os
import stat
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.services.seed_data import seed  # noqa: E402
from app import models  # noqa: F401, E402


def _resolve_sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise SystemExit(f"Refusing to reset non-SQLite database URL: {url.drivername}")
    if not url.database or url.database == ":memory:":
        raise SystemExit("Refusing to reset an in-memory or missing SQLite database path.")

    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = BACKEND_ROOT / db_path
    return db_path.resolve()


def _ensure_inside_backend(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(BACKEND_ROOT)
    except ValueError as exc:
        raise SystemExit(f"Refusing to delete outside backend directory: {resolved}") from exc
    return resolved


def _remove_path(path: Path) -> None:
    resolved = _ensure_inside_backend(path)
    if resolved.is_dir():
        shutil.rmtree(resolved, onexc=_make_writable_and_retry)
        print(f"Removed directory: {resolved}")
    elif resolved.exists():
        resolved.unlink()
        print(f"Removed file: {resolved}")
    else:
        print(f"Already clean: {resolved}")


def _make_writable_and_retry(function, path, excinfo) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
        function(path)
    except Exception:
        raise excinfo[1]


def main() -> None:
    settings = get_settings()
    db_path = _resolve_sqlite_path(settings.database_url)
    upload_root = _ensure_inside_backend(settings.upload_root if settings.upload_root.is_absolute() else BACKEND_ROOT / settings.upload_root)
    generated_root = _ensure_inside_backend(BACKEND_ROOT / "data" / "generated")

    print("Resetting local AI-ME642 demo data.")
    print(f"Backend root: {BACKEND_ROOT}")
    print(f"SQLite database: {db_path}")
    print(f"Upload root: {upload_root}")
    print(f"Generated root: {generated_root}")

    _remove_path(db_path)
    _remove_path(upload_root)
    _remove_path(generated_root)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    try:
        seed(db)
    finally:
        db.close()
        engine.dispose()

    print("")
    print("Demo data reset complete.")
    print("Seed accounts all use password: password123")
    print("- student@example.edu")
    print("- student2@example.edu")
    print("- ta@example.edu")
    print("- instructor@example.edu")
    print("")
    print("Next:")
    print("  uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
    print("  cd ..\\frontend")
    print('  $env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000/api"')
    print("  npm run dev -- --hostname 127.0.0.1 --port 3000")


if __name__ == "__main__":
    main()
