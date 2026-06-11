from __future__ import annotations
from datetime import UTC, datetime
from pathlib import Path
import re
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..deps import current_user, ensure_owner_or_staff
from ..models import Assignment, FileArtifact, ProjectSpecification, Submission, User
from ..schemas import FileArtifactOut, InterpretationIn, SubmissionCreate, SubmissionOut
from ..services.package_builder import build_submission_zip


router = APIRouter(prefix="/submissions", tags=["submissions"])


FILE_TYPES = {
    "lammps_input",
    "lammps_log",
    "readme",
    "prompt_log",
    "python_analysis",
    "ovito_script",
    "slurm_script",
    "figure",
    "data",
    "other",
}


def _clean_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "uploaded_file"


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _get_submission(db: Session, submission_id: int, user: User) -> Submission:
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    ensure_owner_or_staff(submission.user_id, user)
    return submission


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[Submission]:
    query = db.query(Submission)
    if user.role not in {"instructor", "ta"}:
        query = query.filter_by(user_id=user.id)
    return query.order_by(Submission.updated_at.desc()).all()


@router.post("", response_model=SubmissionOut)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Submission:
    assignment = db.get(Assignment, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if payload.project_id:
        project = db.get(ProjectSpecification, payload.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        ensure_owner_or_staff(project.user_id, user)
    existing = db.query(Submission).filter_by(assignment_id=payload.assignment_id, user_id=user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="A submission already exists for this assignment")
    submission = Submission(**payload.model_dump(), user_id=user.id)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Submission:
    return _get_submission(db, submission_id, user)


@router.patch("/{submission_id}/interpretation", response_model=SubmissionOut)
def update_interpretation(
    submission_id: int,
    payload: InterpretationIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Submission:
    submission = _get_submission(db, submission_id, user)
    if user.role in {"instructor", "ta"}:
        raise HTTPException(status_code=403, detail="Only the student owner can edit interpretation")
    submission.student_interpretation = payload.student_interpretation
    db.commit()
    db.refresh(submission)
    return submission


@router.post("/{submission_id}/submit", response_model=SubmissionOut)
def submit(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Submission:
    submission = _get_submission(db, submission_id, user)
    if user.role in {"instructor", "ta"}:
        raise HTTPException(status_code=403, detail="Only the student owner can submit")
    submission.status = "submitted"
    submission.submitted_at = _utc_now()
    db.commit()
    db.refresh(submission)
    return submission


@router.post("/{submission_id}/files", response_model=FileArtifactOut)
async def upload_file(
    submission_id: int,
    file_type: str,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> FileArtifact:
    settings = get_settings()
    submission = _get_submission(db, submission_id, user)
    if user.role in {"instructor", "ta"}:
        raise HTTPException(status_code=403, detail="Only the student owner can upload files")
    if file_type not in FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file_type: {file_type}")

    safe_name = _clean_filename(upload.filename or "uploaded_file")
    extension = Path(safe_name).suffix.lower()
    if extension not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {extension}")

    content = await upload.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file exceeds configured size limit")

    target_dir = settings.upload_root / f"submission_{submission.id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{file_type}_{_utc_now().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
    target_path = target_dir / stored_name
    target_path.write_bytes(content)

    artifact = FileArtifact(
        submission_id=submission.id,
        user_id=user.id,
        original_filename=safe_name,
        stored_filename=stored_name,
        file_path=str(target_path),
        file_type=file_type,
        mime_type=upload.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.get("/{submission_id}/package")
def package_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Response:
    submission = _get_submission(db, submission_id, user)
    data = build_submission_zip(db, submission)
    filename = f"submission_{submission.id}_reproducibility_package.zip"
    return Response(
        data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
