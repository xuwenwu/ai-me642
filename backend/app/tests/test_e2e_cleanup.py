from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Assignment,
    Course,
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
from scripts.cleanup_e2e_data import cleanup_e2e_data


def test_cleanup_e2e_data_removes_only_playwright_records(tmp_path: Path):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    upload_root = tmp_path / "uploads"
    upload_dir = upload_root / "submission_1"
    upload_dir.mkdir(parents=True)
    e2e_file = upload_dir / "lammps_log_sample.log"
    e2e_file.write_text("LAMMPS sample", encoding="utf-8")

    course = Course(code="ME642", title="Materials Modeling", term="Spring 2026")
    e2e_user = User(email="e2e-123@example.edu", full_name="E2E Student e2e-123", role="student", hashed_password="hash")
    normal_user = User(email="student@example.edu", full_name="Ada Student", role="student", hashed_password="hash")
    e2e_section = Section(course=course, name="E2E Section", term="Spring 2026")
    e2e_assignment = Assignment(
        course=course,
        title="E2E NVE Validation e2e-123",
        description="temporary browser test",
        assignment_type="lab",
    )
    normal_assignment = Assignment(
        course=course,
        title="Lab 1: Keep Me",
        description="normal assignment",
        assignment_type="lab",
    )
    db.add_all([course, e2e_user, normal_user, e2e_section, e2e_assignment, normal_assignment])
    db.flush()

    db.add(Enrollment(course_id=course.id, section_id=e2e_section.id, user_id=e2e_user.id, role="student"))
    rubric = Rubric(assignment_id=e2e_assignment.id, title="E2E Rubric")
    db.add(rubric)
    db.flush()
    criterion = RubricCriterion(rubric_id=rubric.id, name="Validation", description="Check evidence", max_points=10, sort_order=1)
    db.add(criterion)
    db.flush()

    project = ProjectSpecification(user_id=e2e_user.id, course_id=course.id, title="E2E Project")
    submission = Submission(assignment_id=e2e_assignment.id, user_id=e2e_user.id, title="E2E package")
    db.add_all([project, submission])
    db.flush()
    db.add(
        FileArtifact(
            submission_id=submission.id,
            user_id=e2e_user.id,
            original_filename="sample.log",
            stored_filename="sample.log",
            file_path=str(e2e_file),
            file_type="lammps_log",
            size_bytes=e2e_file.stat().st_size,
        )
    )
    report = ValidationReport(submission_id=submission.id, status="warning", summary="sample")
    grade = Grade(submission_id=submission.id, grader_id=normal_user.id, rubric_score=9, final_score=9)
    prompt_log = PromptLogEntry(user_id=e2e_user.id, assignment_id=e2e_assignment.id, title="E2E prompt")
    db.add_all([report, grade, prompt_log])
    db.flush()
    db.add_all(
        [
            ValidationCheck(validation_report_id=report.id, check_type="health", status="passed", severity="info", message="ok"),
            CriterionScore(grade_id=grade.id, criterion_id=criterion.id, score=9),
        ]
    )
    db.commit()

    dry_run = cleanup_e2e_data(db, upload_root=upload_root, dry_run=True)
    assert dry_run.users == 1
    assert dry_run.assignments == 1
    assert dry_run.submissions == 1
    assert e2e_file.exists()

    summary = cleanup_e2e_data(db, upload_root=upload_root, dry_run=False)
    assert summary.users == 1
    assert summary.assignments == 1
    assert summary.submissions == 1
    assert summary.files == 1
    assert not e2e_file.exists()
    assert not upload_dir.exists()

    assert db.query(User).filter_by(email="e2e-123@example.edu").first() is None
    assert db.query(Assignment).filter_by(title="E2E NVE Validation e2e-123").first() is None
    assert db.query(Submission).count() == 0
    assert db.query(User).filter_by(email="student@example.edu").one()
    assert db.query(Assignment).filter_by(title="Lab 1: Keep Me").one()

    db.close()
    engine.dispose()
