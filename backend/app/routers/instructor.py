from __future__ import annotations
import csv
import json
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..auth import hash_password
from ..database import get_db
from ..deps import staff_user
from ..models import Assignment, Course, CriterionScore, Enrollment, Grade, Rubric, RubricCriterion, Section, Submission, User
from ..schemas import (
    AssignmentManageIn,
    AssignmentAnalyticsOut,
    AssignmentOut,
    GradeIn,
    GradeOut,
    InstructorAnalyticsOut,
    NeedsAttentionOut,
    RosterImportIn,
    RosterImportOut,
    RosterStudentIn,
    RosterStudentOut,
    RubricCriterionOut,
    SubmissionOut,
)


router = APIRouter(prefix="/instructor", tags=["instructor"])


DEFAULT_CRITERIA = [
    ("Conceptual correctness", 20, "Materials-modeling assumptions, ensemble choice, and scientific framing are correct."),
    ("Script/workflow correctness", 20, "LAMMPS/OVITO/Python workflow is coherent and reproducible."),
    ("Simulation validation", 25, "Validation evidence is complete, physically reasonable, and interpreted accurately."),
    ("Interpretation and communication", 20, "Student explains findings, limitations, and uncertainty clearly."),
    ("Reproducibility and AI disclosure", 15, "Artifacts, README, prompt logs, manual edits, and concerns are documented."),
]


def _latest_validation_status(submission: Submission) -> str:
    return submission.validation_reports[0].status if submission.validation_reports else "not_run"


def _attention_reasons(submission: Submission) -> list[str]:
    reasons: list[str] = []
    latest_status = _latest_validation_status(submission)
    file_types = {file.file_type for file in submission.files}

    if submission.status != "submitted":
        reasons.append("not submitted")
    if latest_status == "not_run":
        reasons.append("validation not run")
    elif latest_status in {"warning", "failed"}:
        reasons.append(f"validation {latest_status}")
    if submission.status == "submitted" and not submission.grade:
        reasons.append("needs grading")
    if not submission.student_interpretation.strip():
        reasons.append("missing interpretation")
    for file_type in submission.assignment.required_file_types:
        if file_type not in file_types:
            reasons.append(f"missing {file_type}")
    return reasons


def _filtered_submissions(
    db: Session,
    assignment_id: int | None,
    status: str | None,
    validation_status: str | None,
    grade_state: str | None,
) -> list[Submission]:
    rows = db.query(Submission).order_by(Submission.assignment_id, Submission.user_id).all()
    filtered: list[Submission] = []
    for submission in rows:
        latest_status = _latest_validation_status(submission)
        graded = submission.grade is not None
        if assignment_id and submission.assignment_id != assignment_id:
            continue
        if status and status != "all" and submission.status != status:
            continue
        if validation_status and validation_status != "all" and latest_status != validation_status:
            continue
        if grade_state and grade_state != "all":
            if grade_state == "graded" and not graded:
                continue
            if grade_state == "ungraded" and graded:
                continue
        filtered.append(submission)
    return filtered


def _default_course(db: Session) -> Course:
    course = db.query(Course).filter_by(code="ME642").first() or db.query(Course).order_by(Course.id).first()
    if not course:
        course = Course(code="ME642", title="Materials Modeling", term="Spring 2026")
        db.add(course)
        db.flush()
    return course


def _section(db: Session, course: Course, name: str) -> Section:
    section_name = name.strip() or "Pilot Section A"
    section = db.query(Section).filter_by(course_id=course.id, name=section_name).first()
    if not section:
        section = Section(course_id=course.id, name=section_name, term=course.term)
        db.add(section)
        db.flush()
    return section


def _assignment_out(assignment: Assignment) -> AssignmentOut:
    criteria = assignment.rubric.criteria if assignment.rubric else []
    return AssignmentOut(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        assignment_type=assignment.assignment_type,
        due_date=assignment.due_date,
        total_points=assignment.total_points,
        status=assignment.status,
        validation_profile=assignment.validation_profile,
        required_file_types=assignment.required_file_types,
        optional_file_types=assignment.optional_file_types,
        validation_settings=assignment.validation_settings,
        interpretation_prompts=assignment.interpretation_prompts,
        criteria=[RubricCriterionOut.model_validate(c) for c in criteria],
    )


def _apply_assignment_payload(assignment: Assignment, payload: AssignmentManageIn) -> None:
    assignment.title = payload.title.strip()
    assignment.description = payload.description
    assignment.assignment_type = payload.assignment_type or "lab"
    assignment.due_date = payload.due_date
    assignment.total_points = payload.total_points
    assignment.status = payload.status
    assignment.validation_profile = payload.validation_profile
    assignment.required_file_types_json = json.dumps(payload.required_file_types)
    assignment.optional_file_types_json = json.dumps(payload.optional_file_types)
    assignment.validation_settings_json = json.dumps(payload.validation_settings)
    assignment.interpretation_prompts_json = json.dumps(payload.interpretation_prompts)


def _ensure_default_rubric(db: Session, assignment: Assignment) -> None:
    rubric = assignment.rubric or db.query(Rubric).filter_by(assignment_id=assignment.id).first()
    if not rubric:
        rubric = Rubric(assignment_id=assignment.id, title=f"{assignment.title} Rubric")
        db.add(rubric)
        db.flush()
    rubric.title = f"{assignment.title} Rubric"
    if not rubric.criteria:
        for order, (name, points, description) in enumerate(DEFAULT_CRITERIA, 1):
            db.add(RubricCriterion(rubric_id=rubric.id, name=name, description=description, max_points=points, sort_order=order))


def _upsert_roster_student(db: Session, payload: RosterStudentIn) -> tuple[User, bool]:
    course = _default_course(db)
    section = _section(db, course, payload.section)
    email = payload.email.strip().lower()
    user = db.query(User).filter_by(email=email).first()
    created = False
    if not user:
        user = User(email=email, full_name=payload.full_name.strip(), role="student", hashed_password=hash_password(payload.password))
        db.add(user)
        db.flush()
        created = True
    else:
        user.full_name = payload.full_name.strip()
        user.role = "student"
        if payload.password:
            user.hashed_password = hash_password(payload.password)

    enrollment = db.query(Enrollment).filter_by(course_id=course.id, user_id=user.id).first()
    if not enrollment:
        enrollment = Enrollment(course_id=course.id, user_id=user.id)
        db.add(enrollment)
    enrollment.section_id = section.id
    enrollment.role = "student"
    enrollment.status = "active"
    return user, created


def _roster_rows(db: Session) -> list[RosterStudentOut]:
    assignments = db.query(Assignment).all()
    total_assignments = len(assignments)
    enrollments = (
        db.query(Enrollment)
        .join(User)
        .filter(Enrollment.role == "student", Enrollment.status == "active")
        .order_by(User.full_name)
        .all()
    )
    rows: list[RosterStudentOut] = []
    for enrollment in enrollments:
        submissions = db.query(Submission).filter_by(user_id=enrollment.user_id).all()
        rows.append(
            RosterStudentOut(
                student_id=enrollment.user_id,
                full_name=enrollment.user.full_name,
                email=enrollment.user.email,
                section=enrollment.section.name if enrollment.section else "",
                total_assignments=total_assignments,
                submissions_count=len(submissions),
                submitted_count=sum(1 for submission in submissions if submission.status == "submitted"),
                graded_count=sum(1 for submission in submissions if submission.grade),
                warning_count=sum(1 for submission in submissions if _latest_validation_status(submission) == "warning"),
                missing_count=max(total_assignments - len({submission.assignment_id for submission in submissions}), 0),
            )
        )
    return rows


@router.get("/submissions", response_model=list[SubmissionOut])
def list_all_submissions(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> list[Submission]:
    return db.query(Submission).order_by(Submission.updated_at.desc()).all()


@router.get("/assignments", response_model=list[AssignmentOut])
def manage_assignments(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> list[AssignmentOut]:
    return [_assignment_out(assignment) for assignment in db.query(Assignment).order_by(Assignment.id).all()]


@router.post("/assignments", response_model=AssignmentOut)
def create_assignment(
    payload: AssignmentManageIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> AssignmentOut:
    course = _default_course(db)
    assignment = Assignment(course_id=course.id, title=payload.title, description=payload.description, assignment_type=payload.assignment_type)
    _apply_assignment_payload(assignment, payload)
    db.add(assignment)
    db.flush()
    _ensure_default_rubric(db, assignment)
    db.commit()
    db.refresh(assignment)
    return _assignment_out(assignment)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: int,
    payload: AssignmentManageIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> AssignmentOut:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    _apply_assignment_payload(assignment, payload)
    _ensure_default_rubric(db, assignment)
    db.commit()
    db.refresh(assignment)
    return _assignment_out(assignment)


@router.get("/analytics", response_model=InstructorAnalyticsOut)
def instructor_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> InstructorAnalyticsOut:
    assignments = db.query(Assignment).order_by(Assignment.id).all()
    student_enrollments = (
        db.query(Enrollment)
        .join(User)
        .filter(Enrollment.role == "student", Enrollment.status == "active")
        .order_by(User.full_name)
        .all()
    )
    student_ids = {enrollment.user_id for enrollment in student_enrollments}
    submissions = db.query(Submission).filter(Submission.user_id.in_(student_ids)).all() if student_ids else []
    submissions_by_assignment: dict[int, list[Submission]] = {}
    for submission in submissions:
        submissions_by_assignment.setdefault(submission.assignment_id, []).append(submission)

    assignment_summaries: list[AssignmentAnalyticsOut] = []
    attention_items: list[NeedsAttentionOut] = []
    total_students = len(student_ids)

    for assignment in assignments:
        rows = submissions_by_assignment.get(assignment.id, [])
        missing_count = max(total_students - len({row.user_id for row in rows}), 0)
        draft_count = sum(1 for row in rows if row.status != "submitted")
        submitted_count = sum(1 for row in rows if row.status == "submitted")
        validation_not_run_count = sum(1 for row in rows if _latest_validation_status(row) == "not_run")
        validation_warning_count = sum(1 for row in rows if _latest_validation_status(row) == "warning")
        validation_failed_count = sum(1 for row in rows if _latest_validation_status(row) == "failed")
        graded_count = sum(1 for row in rows if row.grade)
        ungraded_submitted_count = sum(1 for row in rows if row.status == "submitted" and not row.grade)
        needs_attention_count = missing_count

        for row in rows:
            reasons = _attention_reasons(row)
            if reasons:
                needs_attention_count += 1
                attention_items.append(
                    NeedsAttentionOut(
                        submission_id=row.id,
                        student_id=row.user_id,
                        student_name=row.user.full_name,
                        student_email=row.user.email,
                        assignment_id=assignment.id,
                        assignment_title=assignment.title,
                        status=row.status,
                        validation_status=_latest_validation_status(row),
                        grade_state="graded" if row.grade else "ungraded",
                        reasons=reasons,
                        updated_at=row.updated_at,
                    )
                )

        assignment_summaries.append(
            AssignmentAnalyticsOut(
                assignment_id=assignment.id,
                title=assignment.title,
                due_date=assignment.due_date,
                total_students=total_students,
                missing_count=missing_count,
                draft_count=draft_count,
                submitted_count=submitted_count,
                validation_not_run_count=validation_not_run_count,
                validation_warning_count=validation_warning_count,
                validation_failed_count=validation_failed_count,
                graded_count=graded_count,
                ungraded_submitted_count=ungraded_submitted_count,
                needs_attention_count=needs_attention_count,
            )
        )

    attention_items.sort(key=lambda item: (item.assignment_id, item.student_name, item.submission_id))
    return InstructorAnalyticsOut(
        total_students=total_students,
        total_assignments=len(assignments),
        total_submissions=len(submissions),
        submitted_count=sum(1 for row in submissions if row.status == "submitted"),
        graded_count=sum(1 for row in submissions if row.grade),
        needs_attention_count=sum(item.needs_attention_count for item in assignment_summaries),
        assignments=assignment_summaries,
        needs_attention=attention_items,
    )


@router.get("/roster", response_model=list[RosterStudentOut])
def roster(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> list[RosterStudentOut]:
    return _roster_rows(db)


@router.post("/roster/students", response_model=RosterStudentOut)
def add_roster_student(
    payload: RosterStudentIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> RosterStudentOut:
    user, _ = _upsert_roster_student(db, payload)
    db.commit()
    return next(student for student in _roster_rows(db) if student.student_id == user.id)


@router.post("/roster/import", response_model=RosterImportOut)
def import_roster(
    payload: RosterImportIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> RosterImportOut:
    reader = csv.DictReader(StringIO(payload.csv_text.strip()))
    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors: list[str] = []
    required = {"email", "full_name"}
    if not reader.fieldnames or not required <= {field.strip() for field in reader.fieldnames}:
        raise HTTPException(status_code=400, detail="CSV must include email and full_name columns")

    for line_number, row in enumerate(reader, 2):
        email = (row.get("email") or "").strip()
        full_name = (row.get("full_name") or "").strip()
        section = (row.get("section") or payload.default_section).strip()
        if not email or not full_name:
            skipped_count += 1
            errors.append(f"Line {line_number}: missing email or full_name")
            continue
        _, created = _upsert_roster_student(db, RosterStudentIn(email=email, full_name=full_name, section=section))
        if created:
            created_count += 1
        else:
            updated_count += 1
    db.commit()
    return RosterImportOut(created_count=created_count, updated_count=updated_count, skipped_count=skipped_count, errors=errors)


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
    assignment_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    validation_status: str | None = Query(default=None),
    grade_state: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    rows = _filtered_submissions(db, assignment_id, status, validation_status, grade_state)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "submission_id",
            "student_name",
            "student_email",
            "section",
            "assignment",
            "status",
            "validation_status",
            "rubric_score",
            "late_penalty",
            "final_score",
        ]
    )
    for submission in rows:
        latest_status = _latest_validation_status(submission)
        grade = submission.grade
        enrollment = db.query(Enrollment).filter_by(user_id=submission.user_id, course_id=submission.assignment.course_id).first()
        writer.writerow(
            [
                submission.id,
                submission.user.full_name,
                submission.user.email,
                enrollment.section.name if enrollment and enrollment.section else "",
                submission.assignment.title,
                submission.status,
                latest_status if latest_status != "not_run" else "",
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
