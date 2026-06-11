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


def base_submission(db, log_name="sample_good_nve.log", validation_profile="nve_energy_conservation"):
    user = User(email="student@example.edu", full_name="Ada Student", role="student", hashed_password=hash_password("password123"))
    course = Course(code="ME642", title="Materials Modeling", term="Spring 2026")
    db.add_all([user, course])
    db.flush()
    assignment = Assignment(
        course_id=course.id,
        title="Lab 3: NVE Energy Conservation and Timestep Stability" if validation_profile == "nve_energy_conservation" else "Lab 2: NVT Temperature Control",
        description="Test",
        assignment_type="lab",
        total_points=100,
        validation_profile=validation_profile,
        validation_settings_json='{"energy_drift_warning_threshold": 0.05}' if validation_profile == "nve_energy_conservation" else '{"target_temperature": 300, "temperature_tolerance": 75}',
        required_file_types_json='["lammps_input", "lammps_log"]',
        optional_file_types_json='["readme", "prompt_log", "python_analysis", "ovito_script", "slurm_script", "figure"]',
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


def add_artifact(db, submission, file_type, filename):
    db.add(
        FileArtifact(
            submission_id=submission.id,
            user_id=submission.user_id,
            original_filename=filename,
            stored_filename=filename,
            file_path=str(ROOT / "sample_data" / filename),
            file_type=file_type,
            mime_type="text/plain",
            size_bytes=100,
        )
    )
    db.commit()
    db.refresh(submission)


def test_validation_good_log_has_no_failed_checks():
    db = make_db()
    submission = base_submission(db)

    report = validate_submission(db, submission)

    assert report.status == "warning"
    assert not [check for check in report.checks if check.status == "failed"]
    assert any(check.check_type == "energy_drift" for check in report.checks)
    assert any(check.check_type == "lammps_input_structure" for check in report.checks)
    assert any(check.check_type == "lammps_ensemble_fix" for check in report.checks)
    assert report.thermo_series
    assert report.thermo_series[0]["x_field"] == "Step"
    assert "TotEng" in report.thermo_series[0]["columns"]
    assert report.thermo_series[0]["points"]
    assert report.interpretation_notes
    assert any(note["topic"] == "Energy conservation" for note in report.interpretation_notes)
    assert any(note["status"] == "supported" for note in report.interpretation_notes)


def test_validation_nvt_profile_adds_temperature_control_check():
    db = make_db()
    submission = base_submission(db, validation_profile="nvt_temperature_control")

    report = validate_submission(db, submission)

    check_types = {check.check_type for check in report.checks}
    note_topics = {note["topic"] for note in report.interpretation_notes}
    assert report.validation_profile == "nvt_temperature_control"
    assert "nvt_temperature_control" in check_types
    assert "energy_drift" not in check_types
    assert "NVT temperature control" in note_topics


def test_validation_error_log_fails():
    db = make_db()
    submission = base_submission(db, "sample_error.log")

    report = validate_submission(db, submission)

    assert report.status == "failed"
    assert any(check.check_type == "lammps_log_health" and check.status == "failed" for check in report.checks)
    assert any(note["topic"] == "LAMMPS log health" and note["status"] == "concern" for note in report.interpretation_notes)


def test_validation_lints_rich_scientific_artifacts():
    db = make_db()
    submission = base_submission(db)
    add_artifact(db, submission, "slurm_script", "sample_slurm.sbatch")
    add_artifact(db, submission, "python_analysis", "sample_analysis.py")
    add_artifact(db, submission, "ovito_script", "sample_ovito.py")

    report = validate_submission(db, submission)

    check_types = {check.check_type for check in report.checks}
    note_topics = {note["topic"] for note in report.interpretation_notes}
    assert "slurm_directives" in check_types
    assert "slurm_script_safety" in check_types
    assert "python_analysis_structure" in check_types
    assert "python_analysis_safety" in check_types
    assert "ovito_script_structure" in check_types
    assert "ovito_script_safety" in check_types
    assert "Slurm reproducibility" in note_topics
    assert "Python analysis artifact" in note_topics
    assert "OVITO artifact" in note_topics
    assert not [check for check in report.checks if check.check_type.endswith("_safety") and check.status == "failed"]


def test_validation_compares_multiple_lammps_logs():
    db = make_db()
    submission = base_submission(db)
    add_artifact(db, submission, "lammps_log", "sample_warning.log")

    report = validate_submission(db, submission)

    assert any(check.check_type == "multi_log_comparison" for check in report.checks)
    assert any(note["topic"] == "Multi-run comparison" for note in report.interpretation_notes)
