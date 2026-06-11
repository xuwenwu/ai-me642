from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.auth import hash_password
from app.database import Base
from app.models import Assignment, Course, FileArtifact, PromptLogEntry, Submission, User
from app.services.validation_engine import validate_submission


ROOT = Path(__file__).resolve().parents[3]


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def base_submission(db, log_name="sample_good_nve.log"):
    user = User(email="student@example.edu", full_name="Ada Student", role="student", hashed_password=hash_password("password123"))
    course = Course(code="ME642", title="Materials Modeling", term="Spring 2026")
    db.add_all([user, course])
    db.flush()
    assignment = Assignment(
        course_id=course.id,
        title="Lab 3: NVE Energy Conservation and Timestep Stability",
        description="Test",
        assignment_type="lab",
        total_points=100,
    )
    db.add(assignment)
    db.flush()
    submission = Submission(assignment_id=assignment.id, user_id=user.id, title="Lab 3 package")
    db.add(submission)
    db.flush()
    db.add(
        PromptLogEntry(
            user_id=user.id,
            assignment_id=assignment.id,
            title="Debug NVE energy drift",
            ai_tool_name="ChatGPT",
            prompt_text="Help me inspect an NVE LAMMPS log without hiding assumptions.",
            validation_performed="Compared total-energy drift and checked warnings.",
        )
    )
    db.add(
        FileArtifact(
            submission_id=submission.id,
            user_id=user.id,
            original_filename="sample_input.in",
            stored_filename="sample_input.in",
            file_path=str(ROOT / "sample_data" / "sample_input.in"),
            file_type="lammps_input",
            mime_type="text/plain",
            size_bytes=100,
        )
    )
    db.add(
        FileArtifact(
            submission_id=submission.id,
            user_id=user.id,
            original_filename=log_name,
            stored_filename=log_name,
            file_path=str(ROOT / "sample_data" / log_name),
            file_type="lammps_log",
            mime_type="text/plain",
            size_bytes=100,
        )
    )
    db.commit()
    db.refresh(submission)
    return submission


def test_validation_good_log_has_no_failed_checks():
    db = make_db()
    submission = base_submission(db)

    report = validate_submission(db, submission)

    assert report.status == "warning"
    assert not [check for check in report.checks if check.status == "failed"]
    assert any(check.check_type == "energy_drift" for check in report.checks)


def test_validation_error_log_fails():
    db = make_db()
    submission = base_submission(db, "sample_error.log")

    report = validate_submission(db, submission)

    assert report.status == "failed"
    assert any(check.check_type == "lammps_log_health" and check.status == "failed" for check in report.checks)

