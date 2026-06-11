from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import zipfile

from sqlalchemy.engine import make_url


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402


def _sqlite_path(database_url: str) -> Path | None:
    url = make_url(database_url)
    if url.drivername not in {"sqlite", "sqlite+pysqlite"} or not url.database or url.database == ":memory:":
        return None
    path = Path(url.database)
    return (BACKEND_ROOT / path).resolve() if not path.is_absolute() else path.resolve()


def main() -> None:
    settings = get_settings()
    backup_root = BACKEND_ROOT / "data" / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_root / f"ai_me642_backup_{stamp}.zip"
    db_path = _sqlite_path(settings.database_url)
    upload_root = settings.upload_root if settings.upload_root.is_absolute() else BACKEND_ROOT / settings.upload_root

    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if db_path and db_path.exists():
            zf.write(db_path, f"database/{db_path.name}")
        if upload_root.exists():
            for path in upload_root.rglob("*"):
                if path.is_file():
                    zf.write(path, f"uploads/{path.relative_to(upload_root).as_posix()}")

    print(f"Backup written: {backup_path}")
    if not db_path:
        print("Database URL is not a file-backed SQLite database; database content was not included.")


if __name__ == "__main__":
    main()
