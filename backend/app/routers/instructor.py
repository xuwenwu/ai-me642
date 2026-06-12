from __future__ import annotations
import csv
import json
from io import StringIO
from collections.abc import Mapping
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..auth import hash_password
from ..database import get_db
from ..deps import staff_user
from ..models import AIPolicy, Assignment, Course, CriterionScore, Enrollment, Grade, PromptLogEntry, PromptTemplate, Rubric, RubricCriterion, Section, Submission, User
from ..schemas import (
    AIPolicyIn,
    AIPolicyOut,
    AssignmentManageIn,
    AssignmentAnalyticsOut,
    AssignmentOut,
    GradeIn,
    GradeOut,
    GradebookAssignmentSummaryOut,
    GradebookCellOut,
    GradebookOut,
    GradebookStudentOut,
    InstructorAnalyticsOut,
    NeedsAttentionOut,
    PromptTemplateIn,
    PromptTemplateOut,
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

DEFAULT_ASSISTANT_SYSTEM_PROMPT = (
    "You are a cautious ME642 course assistant. Help students plan checks, debug reasoning, and "
    "interpret validation evidence. Do not fabricate simulation outputs, grades, or final scientific claims."
)

ROSTER_FIELD_ALIASES = {
    "full_name": ("full_name", "name", "student", "student_name", "student name"),
    "email": ("email", "student_email", "student email", "login_id", "login id", "sis login id"),
    "section": ("section", "section_name", "section name"),
}


def _latest_validation_status(submission: Submission) -> str:
    return submission.validation_reports[0].status if submission.validation_reports else "not_run"


def _prompt_logs_for_submission(db: Session, submission: Submission) -> list[PromptLogEntry]:
    return (
        db.query(PromptLogEntry)
        .filter(
            PromptLogEntry.user_id == submission.user_id,
            (PromptLogEntry.assignment_id == submission.assignment_id) | (PromptLogEntry.project_id == submission.project_id),
        )
        .all()
    )


def _has_uploaded_prompt_log(submission: Submission) -> bool:
    return any(file.file_type == "prompt_log" for file in submission.files)


def _ai_disclosure_needs_attention(db: Session, submission: Submission) -> bool:
    if _has_uploaded_prompt_log(submission):
        return False
    prompts = _prompt_logs_for_submission(db, submission)
    if not prompts:
        return True
    for prompt in prompts:
        quality_fields = [
            prompt.ai_output_summary,
            prompt.accepted_parts,
            prompt.rejected_parts,
            prompt.manual_edits,
            prompt.validation_performed,
            prompt.remaining_concerns,
        ]
        if sum(1 for value in quality_fields if value.strip()) >= 3:
            return False
    return True


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


def _attention_reasons_with_ai(db: Session, submission: Submission) -> list[str]:
    reasons = _attention_reasons(submission)
    if _ai_disclosure_needs_attention(db, submission):
        reasons.append("missing or thin AI disclosure")
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


def _filtered_assignments(db: Session, assignment_id: int | None) -> list[Assignment]:
    query = db.query(Assignment).order_by(Assignment.id)
    if assignment_id:
        query = query.filter(Assignment.id == assignment_id)
    return query.all()


def _active_student_enrollments(db: Session) -> list[Enrollment]:
    return (
        db.query(Enrollment)
        .join(User)
        .filter(Enrollment.role == "student", Enrollment.status == "active")
        .order_by(User.full_name)
        .all()
    )


def _gradebook_cell(submission: Submission | None, assignment: Assignment) -> GradebookCellOut:
    if not submission:
        return GradebookCellOut(
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            total_points=assignment.total_points,
        )
    grade = submission.grade
    return GradebookCellOut(
        assignment_id=assignment.id,
        assignment_title=assignment.title,
        total_points=assignment.total_points,
        submission_id=submission.id,
        submission_status=submission.status,
        validation_status=_latest_validation_status(submission),
        grade_state="graded" if grade else "ungraded",
        final_score=grade.final_score if grade else None,
        submitted_at=submission.submitted_at,
        updated_at=submission.updated_at,
    )


def _csv_response(contents: str, filename: str) -> Response:
    return Response(
        contents,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _format_points(value: float) -> str:
    return f"{value:g}"


def _assignment_canvas_column(assignment: GradebookAssignmentSummaryOut) -> str:
    return f"{assignment.title} ({_format_points(assignment.total_points)})"


def _cell_feedback(db: Session, cell: GradebookCellOut) -> str:
    if not cell.submission_id:
        return ""
    submission = db.get(Submission, cell.submission_id)
    return submission.grade.feedback if submission and submission.grade else ""


def _gradebook(db: Session, assignment_id: int | None = None) -> GradebookOut:
    assignments = _filtered_assignments(db, assignment_id)
    enrollments = _active_student_enrollments(db)
    student_ids = [enrollment.user_id for enrollment in enrollments]
    assignment_ids = [assignment.id for assignment in assignments]
    submissions = (
        db.query(Submission)
        .filter(Submission.user_id.in_(student_ids), Submission.assignment_id.in_(assignment_ids))
        .all()
        if student_ids and assignment_ids
        else []
    )
    submission_by_key = {(submission.user_id, submission.assignment_id): submission for submission in submissions}
    assignment_rows: list[GradebookAssignmentSummaryOut] = []
    student_rows: list[GradebookStudentOut] = []

    for assignment in assignments:
        rows = [submission for submission in submissions if submission.assignment_id == assignment.id]
        graded_scores = [submission.grade.final_score for submission in rows if submission.grade]
        assignment_rows.append(
            GradebookAssignmentSummaryOut(
                assignment_id=assignment.id,
                title=assignment.title,
                due_date=assignment.due_date,
                total_points=assignment.total_points,
                submitted_count=sum(1 for submission in rows if submission.status == "submitted"),
                graded_count=len(graded_scores),
                ungraded_count=sum(1 for submission in rows if submission.status == "submitted" and not submission.grade),
                missing_count=max(len(enrollments) - len({submission.user_id for submission in rows}), 0),
                warning_count=sum(1 for submission in rows if _latest_validation_status(submission) == "warning"),
                failed_count=sum(1 for submission in rows if _latest_validation_status(submission) == "failed"),
                average_score=(sum(graded_scores) / len(graded_scores)) if graded_scores else None,
            )
        )

    for enrollment in enrollments:
        cells = [_gradebook_cell(submission_by_key.get((enrollment.user_id, assignment.id)), assignment) for assignment in assignments]
        graded_cells = [cell for cell in cells if cell.final_score is not None]
        possible_score = sum(cell.total_points for cell in cells if cell.final_score is not None)
        current_score = sum(cell.final_score or 0 for cell in graded_cells)
        student_rows.append(
            GradebookStudentOut(
                student_id=enrollment.user_id,
                full_name=enrollment.user.full_name,
                email=enrollment.user.email,
                section=enrollment.section.name if enrollment.section else "",
                submitted_count=sum(1 for cell in cells if cell.submission_status == "submitted"),
                graded_count=len(graded_cells),
                missing_count=sum(1 for cell in cells if cell.submission_status == "missing"),
                warning_count=sum(1 for cell in cells if cell.validation_status == "warning"),
                current_score=current_score,
                possible_score=possible_score,
                assignments=cells,
            )
        )

    total_graded = sum(row.graded_count for row in assignment_rows)
    graded_total = sum(cell.final_score or 0 for row in student_rows for cell in row.assignments if cell.final_score is not None)
    possible_total = sum(cell.total_points for row in student_rows for cell in row.assignments if cell.final_score is not None)
    return GradebookOut(
        total_students=len(enrollments),
        total_assignments=len(assignments),
        total_submitted=sum(row.submitted_count for row in assignment_rows),
        total_graded=total_graded,
        total_missing=sum(row.missing_count for row in assignment_rows),
        current_average_score=(graded_total / possible_total * 100) if possible_total else None,
        assignments=assignment_rows,
        students=student_rows,
    )


def _normalized_csv_row(row: Mapping[str, str | None]) -> dict[str, str]:
    return {key.strip().lower().replace("_", " "): (value or "").strip() for key, value in row.items() if key}


def _csv_value(row: Mapping[str, str], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        value = row.get(alias.replace("_", " "))
        if value:
            return value
    return ""


def _valid_email(value: str) -> bool:
    return "@" in value and "." in value.rsplit("@", 1)[-1]


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


def _policy_out(policy: AIPolicy) -> AIPolicyOut:
    return AIPolicyOut(
        id=policy.id,
        course_id=policy.course_id,
        title=policy.title,
        body=policy.body,
        allowed_tools=policy.allowed_tools,
        disclosure_requirements=policy.disclosure_requirements,
        assistant_enabled=policy.assistant_enabled,
        assistant_provider=policy.assistant_provider,
        assistant_model=policy.assistant_model,
        assistant_system_prompt=policy.assistant_system_prompt,
        assistant_retention_days=policy.assistant_retention_days,
        updated_at=policy.updated_at,
    )


def _template_out(template: PromptTemplate) -> PromptTemplateOut:
    return PromptTemplateOut(
        id=template.id,
        course_id=template.course_id,
        title=template.title,
        task_type=template.task_type,
        prompt_text=template.prompt_text,
        checklist=template.checklist,
        status=template.status,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _ensure_policy(db: Session) -> AIPolicy:
    course = _default_course(db)
    policy = db.query(AIPolicy).filter_by(course_id=course.id).first()
    if not policy:
        policy = AIPolicy(
            course_id=course.id,
            title="ME642 Responsible AI Use Policy",
            body="AI assistance is allowed when students disclose the work, verify outputs, and keep responsibility for final scientific claims.",
            disclosure_requirements_json=json.dumps(
                [
                    "Record the AI tool, task purpose, and prompt or prompt summary.",
                    "Summarize the AI output in your own words.",
                    "Identify accepted and rejected suggestions.",
                    "Describe manual edits and validation performed after AI assistance.",
                    "State remaining concerns or uncertainties before submission.",
                ]
            ),
        )
        db.add(policy)
        db.flush()
    return policy


def _apply_policy_payload(policy: AIPolicy, payload: AIPolicyIn) -> None:
    policy.title = payload.title.strip()
    policy.body = payload.body
    policy.allowed_tools_json = json.dumps(payload.allowed_tools)
    policy.disclosure_requirements_json = json.dumps(payload.disclosure_requirements)
    policy.assistant_enabled = payload.assistant_enabled
    policy.assistant_provider = payload.assistant_provider.strip() or "offline"
    policy.assistant_model = payload.assistant_model.strip()
    policy.assistant_system_prompt = payload.assistant_system_prompt.strip() or DEFAULT_ASSISTANT_SYSTEM_PROMPT
    policy.assistant_retention_days = max(payload.assistant_retention_days, 0)


def _apply_template_payload(template: PromptTemplate, payload: PromptTemplateIn) -> None:
    template.title = payload.title.strip()
    template.task_type = payload.task_type.strip() or "lammps_debugging"
    template.prompt_text = payload.prompt_text
    template.checklist_json = json.dumps(payload.checklist)
    template.status = payload.status or "active"


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


@router.get("/ai-policy", response_model=AIPolicyOut)
def get_ai_policy(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> AIPolicyOut:
    return _policy_out(_ensure_policy(db))


@router.patch("/ai-policy", response_model=AIPolicyOut)
def update_ai_policy(
    payload: AIPolicyIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> AIPolicyOut:
    policy = _ensure_policy(db)
    _apply_policy_payload(policy, payload)
    db.commit()
    db.refresh(policy)
    return _policy_out(policy)


@router.get("/prompt-templates", response_model=list[PromptTemplateOut])
def get_prompt_templates(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> list[PromptTemplateOut]:
    course = _default_course(db)
    rows = db.query(PromptTemplate).filter_by(course_id=course.id).order_by(PromptTemplate.task_type, PromptTemplate.title).all()
    return [_template_out(row) for row in rows]


@router.post("/prompt-templates", response_model=PromptTemplateOut)
def create_prompt_template(
    payload: PromptTemplateIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> PromptTemplateOut:
    course = _default_course(db)
    template = PromptTemplate(course_id=course.id, title=payload.title)
    _apply_template_payload(template, payload)
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_out(template)


@router.patch("/prompt-templates/{template_id}", response_model=PromptTemplateOut)
def update_prompt_template(
    template_id: int,
    payload: PromptTemplateIn,
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> PromptTemplateOut:
    template = db.get(PromptTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    _apply_template_payload(template, payload)
    db.commit()
    db.refresh(template)
    return _template_out(template)


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
        ai_disclosure_missing_count = sum(1 for row in rows if _ai_disclosure_needs_attention(db, row))
        graded_count = sum(1 for row in rows if row.grade)
        ungraded_submitted_count = sum(1 for row in rows if row.status == "submitted" and not row.grade)
        needs_attention_count = missing_count

        for row in rows:
            reasons = _attention_reasons_with_ai(db, row)
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
                ai_disclosure_missing_count=ai_disclosure_missing_count,
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
        ai_disclosure_missing_count=sum(item.ai_disclosure_missing_count for item in assignment_summaries),
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
    normalized_fields = {field.strip().lower().replace("_", " ") for field in reader.fieldnames or []}
    has_name = any(alias.replace("_", " ") in normalized_fields for alias in ROSTER_FIELD_ALIASES["full_name"])
    has_email = any(alias.replace("_", " ") in normalized_fields for alias in ROSTER_FIELD_ALIASES["email"])
    if not reader.fieldnames or not (has_name and has_email):
        raise HTTPException(status_code=400, detail="CSV must include full_name/name and email/login_id columns")

    for line_number, row in enumerate(reader, 2):
        normalized = _normalized_csv_row(row)
        email = _csv_value(normalized, ROSTER_FIELD_ALIASES["email"]).lower()
        full_name = _csv_value(normalized, ROSTER_FIELD_ALIASES["full_name"])
        section = _csv_value(normalized, ROSTER_FIELD_ALIASES["section"]) or payload.default_section
        if not email or not full_name:
            skipped_count += 1
            errors.append(f"Line {line_number}: missing email or full_name")
            continue
        if not _valid_email(email):
            skipped_count += 1
            errors.append(f"Line {line_number}: invalid email/login_id")
            continue
        _, created = _upsert_roster_student(db, RosterStudentIn(email=email, full_name=full_name, section=section))
        if created:
            created_count += 1
        else:
            updated_count += 1
    db.commit()
    return RosterImportOut(created_count=created_count, updated_count=updated_count, skipped_count=skipped_count, errors=errors)


@router.get("/roster.csv")
def roster_csv(
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    rows = _roster_rows(db)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["full_name", "email", "sis_user_id", "section", "submitted_count", "graded_count", "missing_count", "warning_count"])
    for student in rows:
        writer.writerow(
            [
                student.full_name,
                student.email,
                student.email,
                student.section,
                student.submitted_count,
                student.graded_count,
                student.missing_count,
                student.warning_count,
            ]
        )
    return _csv_response(buffer.getvalue(), "roster_export.csv")


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


@router.get("/gradebook", response_model=GradebookOut)
def gradebook(
    assignment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> GradebookOut:
    return _gradebook(db, assignment_id)


@router.get("/course-gradebook.csv")
def course_gradebook_csv(
    assignment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    gradebook_data = _gradebook(db, assignment_id)
    buffer = StringIO()
    writer = csv.writer(buffer)
    headers = ["student_id", "student_name", "student_email", "section", "submitted_count", "graded_count", "missing_count", "current_score", "possible_score"]
    for assignment in gradebook_data.assignments:
        headers.extend([f"{assignment.title} status", f"{assignment.title} validation", f"{assignment.title} score"])
    writer.writerow(headers)
    for student in gradebook_data.students:
        row: list[object] = [
            student.student_id,
            student.full_name,
            student.email,
            student.section,
            student.submitted_count,
            student.graded_count,
            student.missing_count,
            student.current_score,
            student.possible_score,
        ]
        for cell in student.assignments:
            row.extend([cell.submission_status, cell.validation_status, cell.final_score if cell.final_score is not None else ""])
        writer.writerow(row)
    return _csv_response(buffer.getvalue(), "course_gradebook.csv")


@router.get("/canvas-gradebook.csv")
def canvas_gradebook_csv(
    assignment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    gradebook_data = _gradebook(db, assignment_id)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Student", "ID", "SIS User ID", "SIS Login ID", "Section", *[_assignment_canvas_column(assignment) for assignment in gradebook_data.assignments]])
    for student in gradebook_data.students:
        writer.writerow(
            [
                student.full_name,
                "",
                student.email,
                student.email,
                student.section,
                *[cell.final_score if cell.final_score is not None else "" for cell in student.assignments],
            ]
        )
    return _csv_response(buffer.getvalue(), "canvas_gradebook_import.csv")


@router.get("/lms-submission-detail.csv")
def lms_submission_detail_csv(
    assignment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(staff_user),
) -> Response:
    gradebook_data = _gradebook(db, assignment_id)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Student",
            "SIS User ID",
            "SIS Login ID",
            "Section",
            "Assignment",
            "Points Possible",
            "Score",
            "Submission Status",
            "Validation Status",
            "Submitted At",
            "Feedback",
        ]
    )
    for student in gradebook_data.students:
        for cell in student.assignments:
            writer.writerow(
                [
                    student.full_name,
                    student.email,
                    student.email,
                    student.section,
                    cell.assignment_title,
                    cell.total_points,
                    cell.final_score if cell.final_score is not None else "",
                    cell.submission_status,
                    cell.validation_status,
                    cell.submitted_at.isoformat() if cell.submitted_at else "",
                    _cell_feedback(db, cell),
                ]
            )
    return _csv_response(buffer.getvalue(), "lms_submission_detail.csv")


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
    return _csv_response(buffer.getvalue(), "gradebook.csv")
