from __future__ import annotations

from datetime import UTC, datetime
import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import current_user, staff_user
from ..models import PilotFeedback, User
from ..schemas import PilotFeedbackIn, PilotFeedbackOut, PilotFeedbackUpdateIn


router = APIRouter(prefix="/feedback", tags=["feedback"])
staff_router = APIRouter(prefix="/instructor/feedback", tags=["instructor"])

ALLOWED_CATEGORIES = {
    "login_account",
    "upload",
    "validation",
    "ai_guidance",
    "submission",
    "grading_feedback",
    "confusing_ui",
    "other",
}
ALLOWED_SEVERITIES = {"question", "minor_confusion", "blocks_progress"}
ALLOWED_STATUSES = {"new", "reviewing", "resolved", "dismissed"}


def _clean_choice(value: str, allowed: set[str], field_name: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported {field_name}: {value}")
    return cleaned


def _clean_required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return cleaned


def _csv_cell(value: object) -> object:
    if not isinstance(value, str) or not value:
        return value
    if value[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return f"'{value}"
    return value


def _feedback_out(item: PilotFeedback) -> PilotFeedbackOut:
    return PilotFeedbackOut(
        id=item.id,
        user_id=item.user_id,
        user_email=item.user.email,
        user_full_name=item.user.full_name,
        role=item.role,
        page_url=item.page_url,
        category=item.category,
        severity=item.severity,
        message=item.message,
        contact_allowed=item.contact_allowed,
        status=item.status,
        instructor_notes=item.instructor_notes,
        resolved_by_id=item.resolved_by_id,
        resolved_at=item.resolved_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _filtered_feedback(
    db: Session,
    status: str | None,
    category: str | None,
    severity: str | None,
    role: str | None,
) -> list[PilotFeedback]:
    query = db.query(PilotFeedback).join(User, PilotFeedback.user_id == User.id)
    if status and status != "all":
        query = query.filter(PilotFeedback.status == _clean_choice(status, ALLOWED_STATUSES, "status"))
    if category and category != "all":
        query = query.filter(PilotFeedback.category == _clean_choice(category, ALLOWED_CATEGORIES, "category"))
    if severity and severity != "all":
        query = query.filter(PilotFeedback.severity == _clean_choice(severity, ALLOWED_SEVERITIES, "severity"))
    if role and role != "all":
        query = query.filter(PilotFeedback.role == role.strip().lower())
    return query.order_by(PilotFeedback.created_at.desc(), PilotFeedback.id.desc()).all()


@router.post("", response_model=PilotFeedbackOut)
def create_feedback(
    payload: PilotFeedbackIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PilotFeedbackOut:
    feedback = PilotFeedback(
        user_id=user.id,
        role=user.role,
        page_url=payload.page_url.strip()[:1000],
        category=_clean_choice(payload.category, ALLOWED_CATEGORIES, "category"),
        severity=_clean_choice(payload.severity, ALLOWED_SEVERITIES, "severity"),
        message=_clean_required_text(payload.message, "message"),
        contact_allowed=payload.contact_allowed,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return _feedback_out(feedback)


@router.get("", response_model=list[PilotFeedbackOut])
def my_feedback(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[PilotFeedbackOut]:
    rows = (
        db.query(PilotFeedback)
        .filter_by(user_id=user.id)
        .order_by(PilotFeedback.created_at.desc(), PilotFeedback.id.desc())
        .all()
    )
    return [_feedback_out(row) for row in rows]


@staff_router.get("", response_model=list[PilotFeedbackOut])
def list_feedback(
    status: str | None = Query(default="all"),
    category: str | None = Query(default="all"),
    severity: str | None = Query(default="all"),
    role: str | None = Query(default="all"),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> list[PilotFeedbackOut]:
    return [_feedback_out(row) for row in _filtered_feedback(db, status, category, severity, role)]


@staff_router.patch("/{feedback_id}", response_model=PilotFeedbackOut)
def update_feedback(
    feedback_id: int,
    payload: PilotFeedbackUpdateIn,
    db: Session = Depends(get_db),
    staff: User = Depends(staff_user),
) -> PilotFeedbackOut:
    feedback = db.get(PilotFeedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback item not found")
    feedback.status = _clean_choice(payload.status, ALLOWED_STATUSES, "status")
    feedback.instructor_notes = payload.instructor_notes.strip()
    feedback.updated_at = datetime.now(UTC).replace(tzinfo=None)
    if feedback.status in {"resolved", "dismissed"}:
        feedback.resolved_by_id = staff.id
        feedback.resolved_at = datetime.now(UTC).replace(tzinfo=None)
    else:
        feedback.resolved_by_id = None
        feedback.resolved_at = None
    db.commit()
    db.refresh(feedback)
    return _feedback_out(feedback)


@staff_router.get(".csv")
def feedback_csv(
    status: str | None = Query(default="all"),
    category: str | None = Query(default="all"),
    severity: str | None = Query(default="all"),
    role: str | None = Query(default="all"),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    rows = _filtered_feedback(db, status, category, severity, role)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "created_at",
            "updated_at",
            "status",
            "category",
            "severity",
            "role",
            "user_full_name",
            "user_email",
            "page_url",
            "contact_allowed",
            "message",
            "instructor_notes",
            "resolved_at",
        ]
    )
    for item in rows:
        row = [
            item.id,
            item.created_at.isoformat(),
            item.updated_at.isoformat(),
            item.status,
            item.category,
            item.severity,
            item.role,
            item.user.full_name,
            item.user.email,
            item.page_url,
            "yes" if item.contact_allowed else "no",
            item.message,
            item.instructor_notes,
            item.resolved_at.isoformat() if item.resolved_at else "",
        ]
        writer.writerow([_csv_cell(value) for value in row])
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="pilot_feedback.csv"'},
    )
