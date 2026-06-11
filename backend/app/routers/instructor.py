from __future__ import annotations
import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import staff_user
from ..models import CriterionScore, Grade, RubricCriterion, Submission, User
from ..schemas import GradeIn, GradeOut, SubmissionOut


router = APIRouter(prefix="/instructor", tags=["instructor"])


@router.get("/submissions", response_model=list[SubmissionOut])
def list_all_submissions(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> list[Submission]:
    return db.query(Submission).order_by(Submission.updated_at.desc()).all()


@router.post("/grades", response_model=GradeOut)
def save_grade(
    payload: GradeIn,
    db: Session = Depends(get_db),
    grader: User = Depends(staff_user),
) -> Grade:
    submission = db.get(Submission, payload.submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    rubric_score = 0.0
    for item in payload.criterion_scores:
        criterion = db.get(RubricCriterion, item.criterion_id)
        if not criterion:
            raise HTTPException(status_code=404, detail=f"Rubric criterion {item.criterion_id} not found")
        if item.score < 0 or item.score > criterion.max_points:
            raise HTTPException(status_code=400, detail=f"Score for {criterion.name} must be between 0 and {criterion.max_points}")
        rubric_score += item.score

    grade = db.query(Grade).filter_by(submission_id=submission.id).first()
    if not grade:
        grade = Grade(submission_id=submission.id, grader_id=grader.id)
        db.add(grade)
        db.flush()
    else:
        db.query(CriterionScore).filter_by(grade_id=grade.id).delete()
    grade.grader_id = grader.id
    grade.rubric_score = rubric_score
    grade.late_penalty = payload.late_penalty
    grade.final_score = max(rubric_score - payload.late_penalty, 0)
    grade.feedback = payload.feedback
    for item in payload.criterion_scores:
        db.add(CriterionScore(grade_id=grade.id, **item.model_dump()))
    db.commit()
    db.refresh(grade)
    return grade


@router.get("/gradebook.csv")
def gradebook_csv(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    rows = db.query(Submission).order_by(Submission.assignment_id, Submission.user_id).all()
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["submission_id", "student_email", "assignment", "status", "validation_status", "rubric_score", "late_penalty", "final_score"])
    for submission in rows:
        latest = submission.validation_reports[0] if submission.validation_reports else None
        grade = submission.grade
        writer.writerow(
            [
                submission.id,
                submission.user.email,
                submission.assignment.title,
                submission.status,
                latest.status if latest else "",
                grade.rubric_score if grade else "",
                grade.late_penalty if grade else "",
                grade.final_score if grade else "",
            ]
        )
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="gradebook.csv"'},
    )

