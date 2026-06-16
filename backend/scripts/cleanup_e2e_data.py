from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Assignment,
    CriterionScore,
    Enrollment,
    FileArtifact,
    Grade,
    ProjectSpecification,
    PromptLogEntry,
    Rubric,
    RubricCriterion,
    Section,
    Submission,
    User,
    ValidationCheck,
    ValidationReport,
)


@dataclass(frozen=True)
class E2ETargets:
    user_ids: list[int]
    assignment_ids: list[int]
    submission_ids: list[int]
    file_paths: list[Path]


@dataclass(frozen=True)
class CleanupSummary:
    users: int
    assignments: int
    submissions: int
    files: int
    upload_dirs: int


def _ids(rows: list[object]) -> list[int]:
    return [int(getattr(row, "id")) for row in rows]


def collect_e2e_targets(db: Session) -> E2ETargets:
    users = (
        db.query(User)
        .filter(or_(User.email.like("e2e-%@example.edu"), User.full_name.like("E2E Student e2e-%")))
        .all()
    )
    assignments = db.query(Assignment).filter(Assignment.title.like("E2E NVE Validation e2e-%")).all()
    user_ids = _ids(users)
    assignment_ids = _ids(assignments)

    submission_query = db.query(Submission)
    if user_ids and assignment_ids:
        submission_query = submission_query.filter(or_(Submission.user_id.in_(user_ids), Submission.assignment_id.in_(assignment_ids)))
    elif user_ids:
        submission_query = submission_query.filter(Submission.user_id.in_(user_ids))
    elif assignment_ids:
        submission_query = submission_query.filter(Submission.assignment_id.in_(assignment_ids))
    else:
        submission_query = submission_query.filter(False)
    submission_ids = _ids(submission_query.all())

    file_paths: list[Path] = []
    if submission_ids:
        artifacts = db.query(FileArtifact).filter(FileArtifact.submission_id.in_(submission_ids)).all()
        file_paths = [Path(artifact.file_path) for artifact in artifacts]

    return E2ETargets(
        user_ids=user_ids,
        assignment_ids=assignment_ids,
        submission_ids=submission_ids,
        file_paths=file_paths,
    )


def _delete_for_ids(db: Session, model: type, column, ids: list[int]) -> int:
    if not ids:
        return 0
    return db.query(model).filter(column.in_(ids)).delete(synchronize_session=False)


def _resolve_upload_path(path: Path, upload_root: Path) -> Path | None:
    resolved_root = upload_root.resolve()
    resolved = (BACKEND_ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def _remove_e2e_files(paths: list[Path], upload_root: Path, dry_run: bool) -> tuple[int, int]:
    removed_files = 0
    candidate_dirs: set[Path] = set()
    for path in paths:
        resolved = _resolve_upload_path(path, upload_root)
        if not resolved:
            continue
        candidate_dirs.add(resolved.parent)
        if resolved.exists():
            removed_files += 1
            if not dry_run:
                resolved.unlink()

    removed_dirs = 0
    for directory in sorted(candidate_dirs, key=lambda item: len(item.parts), reverse=True):
        if directory.exists() and directory.is_dir() and not any(directory.iterdir()):
            removed_dirs += 1
            if not dry_run:
                directory.rmdir()

    return removed_files, removed_dirs


def delete_e2e_targets(db: Session, targets: E2ETargets, upload_root: Path, dry_run: bool = True) -> CleanupSummary:
    file_count, dir_count = _remove_e2e_files(targets.file_paths, upload_root, dry_run=dry_run)

    rubric_ids = _ids(db.query(Rubric).filter(Rubric.assignment_id.in_(targets.assignment_ids)).all()) if targets.assignment_ids else []
    criterion_ids = _ids(db.query(RubricCriterion).filter(RubricCriterion.rubric_id.in_(rubric_ids)).all()) if rubric_ids else []
    report_ids = _ids(db.query(ValidationReport).filter(ValidationReport.submission_id.in_(targets.submission_ids)).all()) if targets.submission_ids else []
    grade_ids = _ids(db.query(Grade).filter(Grade.submission_id.in_(targets.submission_ids)).all()) if targets.submission_ids else []

    if dry_run:
        return CleanupSummary(
            users=len(targets.user_ids),
            assignments=len(targets.assignment_ids),
            submissions=len(targets.submission_ids),
            files=file_count,
            upload_dirs=dir_count,
        )

    _delete_for_ids(db, ValidationCheck, ValidationCheck.validation_report_id, report_ids)
    _delete_for_ids(db, ValidationReport, ValidationReport.submission_id, targets.submission_ids)
    _delete_for_ids(db, CriterionScore, CriterionScore.grade_id, grade_ids)
    _delete_for_ids(db, CriterionScore, CriterionScore.criterion_id, criterion_ids)
    _delete_for_ids(db, Grade, Grade.submission_id, targets.submission_ids)
    _delete_for_ids(db, FileArtifact, FileArtifact.submission_id, targets.submission_ids)

    if targets.user_ids or targets.assignment_ids:
        prompt_query = db.query(PromptLogEntry)
        if targets.user_ids and targets.assignment_ids:
            prompt_query = prompt_query.filter(or_(PromptLogEntry.user_id.in_(targets.user_ids), PromptLogEntry.assignment_id.in_(targets.assignment_ids)))
        elif targets.user_ids:
            prompt_query = prompt_query.filter(PromptLogEntry.user_id.in_(targets.user_ids))
        else:
            prompt_query = prompt_query.filter(PromptLogEntry.assignment_id.in_(targets.assignment_ids))
        prompt_query.delete(synchronize_session=False)

    _delete_for_ids(db, Submission, Submission.id, targets.submission_ids)
    _delete_for_ids(db, ProjectSpecification, ProjectSpecification.user_id, targets.user_ids)
    _delete_for_ids(db, Enrollment, Enrollment.user_id, targets.user_ids)
    _delete_for_ids(db, User, User.id, targets.user_ids)
    _delete_for_ids(db, RubricCriterion, RubricCriterion.rubric_id, rubric_ids)
    _delete_for_ids(db, Rubric, Rubric.assignment_id, targets.assignment_ids)
    _delete_for_ids(db, Assignment, Assignment.id, targets.assignment_ids)

    empty_e2e_sections = (
        db.query(Section)
        .outerjoin(Enrollment, Enrollment.section_id == Section.id)
        .filter(Section.name == "E2E Section", Enrollment.id.is_(None))
        .all()
    )
    for section in empty_e2e_sections:
        db.delete(section)

    db.commit()
    return CleanupSummary(
        users=len(targets.user_ids),
        assignments=len(targets.assignment_ids),
        submissions=len(targets.submission_ids),
        files=file_count,
        upload_dirs=dir_count,
    )


def cleanup_e2e_data(db: Session, upload_root: Path, dry_run: bool = True) -> CleanupSummary:
    return delete_e2e_targets(db, collect_e2e_targets(db), upload_root, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove Playwright E2E test data created by frontend/e2e.")
    parser.add_argument("--confirm", action="store_true", help="Actually delete matching data. Without this flag, only report counts.")
    args = parser.parse_args()

    settings = get_settings()
    upload_root = settings.upload_root if settings.upload_root.is_absolute() else BACKEND_ROOT / settings.upload_root
    dry_run = not args.confirm
    db = SessionLocal()
    try:
        summary = cleanup_e2e_data(db, upload_root=upload_root, dry_run=dry_run)
    finally:
        db.close()

    action = "Would remove" if dry_run else "Removed"
    print(f"{action} {summary.users} E2E users")
    print(f"{action} {summary.assignments} E2E assignments")
    print(f"{action} {summary.submissions} E2E submissions")
    print(f"{action} {summary.files} uploaded E2E files")
    print(f"{action} {summary.upload_dirs} empty E2E upload directories")
    if dry_run:
        print("")
        print("Dry run only. Re-run with --confirm to delete these records.")


if __name__ == "__main__":
    main()
