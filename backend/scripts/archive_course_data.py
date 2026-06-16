from __future__ import annotations

from datetime import datetime
import csv
import json
import os
from pathlib import Path
import sys
import zipfile


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.models import Assignment, Enrollment, FileArtifact, Grade, PromptLogEntry, Submission, User  # noqa: E402


def _archive_root() -> Path:
    settings = get_settings()
    raw = os.getenv("ARCHIVE_ROOT") or os.getenv("BACKUP_ROOT")
    if raw:
      path = Path(raw)
      return path if path.is_absolute() else BACKEND_ROOT / path
    upload_root = settings.upload_root if settings.upload_root.is_absolute() else BACKEND_ROOT / settings.upload_root
    return upload_root.parent / "archives" if upload_root.is_absolute() else BACKEND_ROOT / "data" / "archives"


def _write_csv(zf: zipfile.ZipFile, name: str, headers: list[str], rows: list[list[object]]) -> None:
    buffer = []
    class _Writer:
        def write(self, value: str) -> None:
            buffer.append(value)
    writer = csv.writer(_Writer())
    writer.writerow(headers)
    writer.writerows(rows)
    zf.writestr(name, "".join(buffer))


def main() -> None:
    init_db()
    archive_root = _archive_root()
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = archive_root / f"ai_me642_course_archive_{stamp}.zip"

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        enrollments = db.query(Enrollment).order_by(Enrollment.id).all()
        assignments = db.query(Assignment).order_by(Assignment.id).all()
        submissions = db.query(Submission).order_by(Submission.id).all()
        grades = db.query(Grade).order_by(Grade.id).all()
        prompts = db.query(PromptLogEntry).order_by(PromptLogEntry.id).all()
        files = db.query(FileArtifact).order_by(FileArtifact.id).all()

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            manifest = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "users": len(users),
                "assignments": len(assignments),
                "submissions": len(submissions),
                "grades": len(grades),
                "prompt_logs": len(prompts),
                "files": len(files),
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            _write_csv(
                zf,
                "users.csv",
                ["id", "email", "full_name", "role", "is_active", "must_change_password", "created_at"],
                [[u.id, u.email, u.full_name, u.role, u.is_active, u.must_change_password, u.created_at] for u in users],
            )
            _write_csv(
                zf,
                "enrollments.csv",
                ["id", "course_id", "section_id", "user_id", "role", "status"],
                [[e.id, e.course_id, e.section_id or "", e.user_id, e.role, e.status] for e in enrollments],
            )
            _write_csv(
                zf,
                "assignments.csv",
                ["id", "title", "status", "validation_profile", "total_points", "due_date"],
                [[a.id, a.title, a.status, a.validation_profile, a.total_points, a.due_date or ""] for a in assignments],
            )
            _write_csv(
                zf,
                "submissions.csv",
                ["id", "assignment_id", "user_id", "title", "status", "submitted_at", "updated_at"],
                [[s.id, s.assignment_id, s.user_id, s.title, s.status, s.submitted_at or "", s.updated_at] for s in submissions],
            )
            _write_csv(
                zf,
                "grades.csv",
                ["id", "submission_id", "grader_id", "rubric_score", "late_penalty", "final_score", "graded_at"],
                [[g.id, g.submission_id, g.grader_id, g.rubric_score, g.late_penalty, g.final_score, g.graded_at] for g in grades],
            )
            _write_csv(
                zf,
                "prompt_logs.csv",
                [
                    "id",
                    "user_id",
                    "assignment_id",
                    "project_id",
                    "title",
                    "task_type",
                    "provider_status",
                    "provider_model",
                    "provider_response_id",
                    "provider_input_tokens",
                    "provider_output_tokens",
                    "provider_total_tokens",
                    "created_at",
                ],
                [
                    [
                        p.id,
                        p.user_id,
                        p.assignment_id or "",
                        p.project_id or "",
                        p.title,
                        p.task_type,
                        p.provider_status,
                        p.provider_model,
                        p.provider_response_id,
                        p.provider_input_tokens,
                        p.provider_output_tokens,
                        p.provider_total_tokens,
                        p.created_at,
                    ]
                    for p in prompts
                ],
            )
            for file in files:
                source = Path(file.file_path)
                if source.exists() and source.is_file():
                    zf.write(source, f"uploaded_files/{file.id}_{source.name}")
    finally:
        db.close()

    print(f"Course archive written: {archive_path}")


if __name__ == "__main__":
    main()
